import copy
import io
import json
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from editorial.models import LearningUnitVersion, LearningUnit, Topic
from editorial.services import CHECKS, publish, withdraw, replacement_draft
from accounts.tests import AccessCase
from .admin import TOKEN_SALT
from .models import GenerationJob, DailyQuota
from .provider import generate_text, GenerationFailure, UncertainGeneration
from .services import enqueue, import_draft, process_one, recover_interrupted, INPUT_FIELDS
from .worker_lock import worker_lock

AI_SETTINGS = dict(AI_TEXT_MODELS=[], AI_GENERATION_ENABLED=True, OPENAI_API_KEY="fixture-not-a-real-key", AI_TEXT_MODEL="fixture-model", AI_DAILY_JOB_LIMIT=5, AI_REQUEST_TIMEOUT=60)


def output(questions=False):
    return {"title": "Club Cell", "card_text": "The membrane is the bouncer. It controls movement into and out of the cell.",
        "verification_notes": "Human must check the analogy, objective and supplied references.",
        "questions": [{"prompt": f"Fixture question {i}", "choices": {"a": "Membrane", "b": "Wall", "c": "Nucleus", "d": "Chloroplast"},
                       "correct_choice": "a", "explanation": "The membrane regulates movement."} for i in range(3)] if questions else []}


def response(questions=False):
    return {"output": output(questions), "response_id": "resp_fixture", "usage": {"input_tokens": 100, "output_tokens": 50}}


@override_settings(**AI_SETTINGS)
class GenerationTests(TestCase):
    def setUp(self):
        call_command("seed_demo", stdout=io.StringIO())
        self.topic = LearningUnitVersion.objects.first().topic
        self.staff = get_user_model().objects.create_user("generator", is_staff=True)
        self.staff.user_permissions.add(*Permission.objects.filter(codename__in=["generate_content", "view_generationjob", "publish_learningunitversion"]))
        self.browser = Client()
        self.browser.force_login(self.staff)

    def values(self, questions=False):
        return {"topic": self.topic, "objective": "Explain membrane function.", "brief": "A funny club bouncer analogy.",
            "syllabus_reference": "https://ibass.jamb.gov.ng/assets/uploads/Biology.pdf", "syllabus_excerpt": "Fixture objective: relate cell structures to functions.",
            "source_reference": "Checked test fixture, not real review evidence.", "source_excerpt": "Cell membranes regulate movement into and out of cells.",
            "format": "text", "include_questions": questions, "model_name": "fixture-model"}

    def job(self, questions=False):
        return enqueue(self.staff, uuid.uuid4(), self.values(questions))

    def form(self):
        page = self.browser.get(reverse("admin:generation_generationjob_add"))
        self.assertEqual(page.status_code, 200)
        values = self.values()
        values["topic"] = self.topic.pk
        values["request_token"] = page.context["form"].initial["request_token"]
        return values

    @override_settings(AI_TEXT_MODELS=["fixture-model", "other-text-model"])
    def test_model_dropdown_choice_is_saved_and_unlisted_models_rejected(self):
        page = self.browser.get(reverse("admin:generation_generationjob_add"))
        self.assertEqual(list(page.context["form"].fields["model_name"].choices),
                         [("fixture-model", "fixture-model"), ("other-text-model", "other-text-model")])
        values = self.form()
        values["model_name"] = "other-text-model"
        self.assertEqual(self.browser.post(reverse("admin:generation_generationjob_add"), values).status_code, 302)
        job = GenerationJob.objects.get()
        self.assertEqual(job.model_name, "other-text-model")
        with self.assertRaises(ValidationError):
            enqueue(self.staff, uuid.uuid4(), {**self.values(), "model_name": "unlisted-model"})
        with self.assertRaises(ValidationError):
            enqueue(self.staff, job.pk, {**self.values(), "model_name": "fixture-model"})
        with patch("generation.services.generate_text", return_value=response()) as provider:
            process_one()
            self.assertEqual(provider.call_args.args[0].model_name, "other-text-model")

    def test_admin_submits_a_saved_job_without_calling_provider_and_double_click_reuses_it(self):
        values = self.form()
        with patch("generation.services.generate_text") as provider:
            for _ in range(2):
                result = self.browser.post(reverse("admin:generation_generationjob_add"), values)
                self.assertEqual(result.status_code, 302)
            provider.assert_not_called()
        self.assertEqual(GenerationJob.objects.count(), 1)
        self.assertEqual(DailyQuota.objects.get().used, 1)
        job = GenerationJob.objects.get()
        self.assertEqual(job.status, "queued")
        self.assertFalse(job.include_questions)
        self.assertEqual(job.context["examination"], "JAMB")
        self.assertContains(self.browser.get(result.url), "Queued")

    def test_staff_permission_and_signed_form_binding_are_enforced(self):
        values = self.form()
        other = get_user_model().objects.create_user("other-staff", is_staff=True)
        self.browser.force_login(other)
        self.assertEqual(self.browser.get(reverse("admin:generation_generationjob_add")).status_code, 403)
        with self.assertRaises(PermissionDenied):
            enqueue(other, uuid.uuid4(), self.values())
        other.user_permissions.add(Permission.objects.get(codename="generate_content"))
        self.assertEqual(self.browser.post(reverse("admin:generation_generationjob_add"), values).status_code, 403)
        self.assertEqual(GenerationJob.objects.count(), 0)
        self.browser.logout()
        self.assertEqual(self.browser.get(reverse("admin:generation_generationjob_add")).status_code, 302)

    def test_private_job_details_are_not_readable_by_unprivileged_staff_or_candidates(self):
        job = self.job()
        url = reverse("admin:generation_generationjob_change", args=[job.pk])
        stranger = get_user_model().objects.create_user("no-job-permissions", is_staff=True)
        self.browser.force_login(stranger)
        self.assertEqual(self.browser.get(url).status_code, 403)
        stranger.is_staff = False
        stranger.save()
        self.assertEqual(self.browser.get(url).status_code, 302)

    def test_invalid_expired_and_tampered_forms_do_not_create_jobs(self):
        values = self.form()
        values["request_token"] = "forged"
        self.assertContains(self.browser.post(reverse("admin:generation_generationjob_add"), values), "expired or is invalid")
        with patch("django.core.signing.time.time", return_value=1):
            values["request_token"] = signing.dumps({"id": str(uuid.uuid4()), "user": self.staff.pk}, salt=TOKEN_SALT)
        self.assertContains(self.browser.post(reverse("admin:generation_generationjob_add"), values), "expired or is invalid")
        values = self.form()
        values["format"] = "image"
        self.assertEqual(self.browser.post(reverse("admin:generation_generationjob_add"), values).status_code, 200)
        self.assertEqual(GenerationJob.objects.count(), 0)

    def test_duplicate_id_with_changed_input_is_rejected_and_quota_is_global(self):
        with override_settings(AI_DAILY_JOB_LIMIT=1):
            request_id = uuid.uuid4()
            first = enqueue(self.staff, request_id, self.values())
            self.assertEqual(enqueue(self.staff, request_id, self.values()).pk, first.pk)
            with self.assertRaises(ValidationError):
                enqueue(self.staff, request_id, {**self.values(), "brief": "Changed request"})
            other = get_user_model().objects.create_user("quota-staff", is_staff=True)
            other.user_permissions.add(Permission.objects.get(codename="generate_content"))
            with self.assertRaises(ValidationError):
                enqueue(other, uuid.uuid4(), self.values())
        self.assertEqual(GenerationJob.objects.count(), 1)
        self.assertEqual(DailyQuota.objects.get().used, 1)

    def test_missing_config_or_unsupported_format_reserves_nothing(self):
        for values in [{"AI_GENERATION_ENABLED": False}, {"OPENAI_API_KEY": ""}, {"AI_TEXT_MODEL": ""}, {"AI_DAILY_JOB_LIMIT": 0}]:
            with override_settings(**values), self.assertRaises(ValidationError):
                self.job()
        with self.assertRaises(ValidationError):
            enqueue(self.staff, uuid.uuid4(), {**self.values(), "format": "video"})
        self.assertEqual(DailyQuota.objects.count(), 0)

    def test_text_import_is_atomic_unreviewed_and_never_published(self):
        job = self.job()
        result = response()
        result["output"].update(status="published", accuracy_checked=True)
        with patch("generation.services.generate_text", return_value=result) as provider:
            self.assertTrue(process_one())
            self.assertFalse(process_one())
            provider.assert_called_once()
        job.refresh_from_db()
        self.assertEqual(job.status, "ready")
        version = job.result_version
        self.assertEqual(version.status, "draft")
        self.assertEqual(version.cards.count(), 1)
        self.assertEqual(version.questions.count(), 0)
        self.assertTrue(all(not getattr(version, field) for field in CHECKS))
        self.assertIsNone(version.published_at)
        self.assertEqual(version.source_reference, self.values()["source_reference"])
        self.assertEqual(job.provider_response_id, "resp_fixture")
        self.assertEqual(import_draft(job.pk).pk, version.pk)
        self.assertEqual(LearningUnit.objects.filter(key__startswith="ai-").count(), 1)
        with self.assertRaises(ValidationError):
            publish(version.pk, self.staff)

    def test_requested_questions_import_exactly_three_with_explanations(self):
        job = self.job(True)
        process_one(lambda _: response(True))
        job.refresh_from_db()
        self.assertEqual(job.status, "ready")
        self.assertEqual(list(job.result_version.questions.values_list("position", flat=True)), [1, 2, 3])
        self.assertTrue(job.result_version.questions.get(position=1).explanation)

    def test_malformed_outputs_are_retained_but_never_partially_imported(self):
        cases = []
        bad = response(True); bad["output"]["questions"] = bad["output"]["questions"][:2]; cases.append(bad)
        bad = response(True); bad["output"]["questions"][0]["choices"]["b"] = "Membrane"; cases.append(bad)
        bad = response(True); bad["output"]["card_text"] = "x" * 901; cases.append(bad)
        for result in cases:
            job = self.job(True)
            process_one(lambda _: result)
            job.refresh_from_db()
            self.assertEqual(job.status, "needs_checking")
            self.assertIsNone(job.result_version_id)
            self.assertTrue(job.output)
        self.assertFalse(LearningUnit.objects.filter(key__startswith="ai-").exists())

    def test_question_count_must_match_checkbox(self):
        job = self.job(False)
        process_one(lambda _: response(True))
        job.refresh_from_db()
        self.assertEqual(job.status, "needs_checking")
        self.assertFalse(LearningUnit.objects.filter(key__startswith="ai-").exists())

    def test_interrupted_import_rolls_back_new_content_and_keeps_saved_result(self):
        job = self.job(True)
        with patch("generation.services.Question.objects.create", side_effect=ValidationError("fixture failure")):
            process_one(lambda _: response(True))
        job.refresh_from_db()
        self.assertEqual(job.status, "needs_checking")
        self.assertFalse(LearningUnit.objects.filter(key__startswith="ai-").exists())
        self.assertTrue(job.output)

    def test_worker_restart_marks_uncertain_calls_and_imports_saved_response_without_provider(self):
        uncertain = self.job()
        GenerationJob.objects.filter(pk=uncertain.pk).update(status="running")
        saved = self.job()
        GenerationJob.objects.filter(pk=saved.pk).update(status="received", output=output(), provider_response_id="resp_saved")
        self.assertEqual(recover_interrupted(), 1)
        provider = Mock(side_effect=AssertionError("Must not call provider"))
        self.assertTrue(process_one(provider))
        provider.assert_not_called()
        uncertain.refresh_from_db(); saved.refresh_from_db()
        self.assertEqual(uncertain.status, "needs_checking")
        self.assertEqual(saved.status, "ready")

    def test_uncertain_timeout_is_not_requeued_and_raw_errors_are_not_logged(self):
        job = self.job()
        with patch("generation.services.generate_text", side_effect=UncertainGeneration("Provider reply was not confirmed.")) as provider:
            process_one(); process_one()
            provider.assert_called_once()
        job.refresh_from_db()
        self.assertEqual(job.status, "needs_checking")
        other = self.job()
        process_one(Mock(side_effect=RuntimeError("private provider body and key")))
        other.refresh_from_db()
        self.assertNotIn("private provider body", other.message)
        self.assertEqual(other.status, "needs_checking")

    def test_revoked_generator_and_changed_topic_are_not_sent_to_provider(self):
        job = self.job()
        self.staff.is_active = False; self.staff.save()
        provider = Mock()
        process_one(provider)
        provider.assert_not_called()
        job.refresh_from_db(); self.assertEqual(job.status, "failed")
        self.staff.is_active = True; self.staff.save()
        job = self.job()
        self.topic.name = "Changed topic"; self.topic.save()
        process_one(provider)
        provider.assert_not_called()
        job.refresh_from_db(); self.assertEqual(job.status, "failed")

    def test_jobs_are_read_only_and_the_worker_lock_is_exclusive(self):
        job = self.job()
        url = reverse("admin:generation_generationjob_change", args=[job.pk])
        self.assertEqual(self.browser.post(url, {"status": "ready"}).status_code, 403)
        with tempfile.TemporaryDirectory() as folder, override_settings(BASE_DIR=Path(folder)):
            with worker_lock():
                with self.assertRaises(CommandError), worker_lock():
                    pass
            with worker_lock():
                pass
            with override_settings(AI_GENERATION_ENABLED=False), self.assertRaises(CommandError):
                call_command("generation_worker", once=True, stdout=io.StringIO())

    def test_worker_once_finishes_a_mocked_job(self):
        job = self.job()
        with tempfile.TemporaryDirectory() as folder, override_settings(BASE_DIR=Path(folder)), patch("generation.services.generate_text", return_value=response()):
            call_command("generation_worker", once=True, stdout=io.StringIO())
        job.refresh_from_db(); self.assertEqual(job.status, "ready")

    def test_provider_uses_structured_output_without_sdk_retries_or_storage(self):
        job = self.job()
        result = SimpleNamespace(status="completed", output_text=json.dumps(output()), id="resp_mock", usage=None)
        with patch("generation.provider.OpenAI") as sdk:
            sdk.return_value.__enter__.return_value.responses.create.return_value = result
            received = generate_text(job)
            self.assertEqual(received["response_id"], "resp_mock")
            self.assertEqual(sdk.call_args.kwargs["max_retries"], 0)
            kwargs = sdk.return_value.__enter__.return_value.responses.create.call_args.kwargs
            self.assertFalse(kwargs["store"])
            self.assertTrue(kwargs["text"]["format"]["strict"])
            self.assertNotIn("fixture-not-a-real-key", kwargs["input"])
            self.assertNotIn("generator", kwargs["input"])

    def test_provider_refusal_incomplete_and_network_error_are_safe(self):
        from openai import APITimeoutError, APIStatusError
        job = self.job()
        with patch("generation.provider.OpenAI") as sdk:
            method = sdk.return_value.__enter__.return_value.responses.create
            method.return_value = SimpleNamespace(status="incomplete", output_text="", id="resp_incomplete", usage=None)
            with self.assertRaises(GenerationFailure) as failure:
                generate_text(job)
            self.assertEqual(failure.exception.response_id, "resp_incomplete")
            method.return_value = SimpleNamespace(status="completed", output_text="", id="resp_refusal", usage=None)
            with self.assertRaises(GenerationFailure):
                generate_text(job)
            method.side_effect = APITimeoutError(request=Mock())
            with self.assertRaises(UncertainGeneration):
                generate_text(job)
            method.side_effect = APIStatusError("private provider body", response=Mock(status_code=429, request=Mock()), body={})
            with self.assertRaises(GenerationFailure) as failure:
                generate_text(job)
            self.assertNotIn("private provider body", str(failure.exception))


class OptionalQuizTests(AccessCase):
    def setUp(self):
        super().setUp()
        call_command("seed_demo", stdout=io.StringIO())
        self.version = LearningUnitVersion.objects.get(unit__key="demo-cell-comparison")
        self.reviewer = get_user_model().objects.create_user("optional-reviewer", is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="publish_learningunitversion"))
        for field in CHECKS:
            setattr(self.version, field, True)
        self.version.source_reference = "Checked fixture"
        self.version.review_notes = "Automated fixture only"
        self.version.save()
        for question in self.version.questions.all():
            question.delete()
        publish(self.version.pk, self.reviewer)
        self.sign_in()

    def test_zero_question_posts_are_published_visible_and_not_quiz_ready(self):
        detail = self.client.get(f"/api/v1/units/{self.version.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertFalse(detail.data["quiz_available"])
        feed = self.client.get("/api/v1/feed/", {"subjects": self.version.topic.subject_id}).data
        self.assertEqual(feed["count"], 1)
        self.assertFalse(feed["results"][0]["quiz_available"])
        self.assertEqual(self.client.get("/api/v1/subjects/").data["count"], 1)
        self.assertEqual(self.client.get(f"/api/v1/units/{self.version.pk}/quiz/").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/attempts/", {"version": self.version.pk, "submission_id": str(uuid.uuid4()),
            "answers": [{"question_id": i, "choice": "a"} for i in [1, 2, 3]]}, format="json").status_code, 404)
        for key in ["questions", "correct_choice", "ai_provenance"]:
            self.assertNotIn(key, detail.data)

    def test_one_or_two_questions_still_block_publication(self):
        from editorial.models import Question
        draft = replacement_draft(self.version.pk)
        for field in CHECKS:
            setattr(draft, field, True)
        draft.review_notes = "Checked fixture"; draft.save()
        for position in [1, 2]:
            Question.objects.create(version=draft, position=position, prompt="Fixture", choice_a="A", choice_b="B", choice_c="C", choice_d="D", correct_choice="a", explanation="Fixture explanation")
            with self.assertRaises(ValidationError):
                publish(draft.pk, self.reviewer)
