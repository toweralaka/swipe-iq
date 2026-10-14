import copy
import uuid
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from accounts.tests import AccessCase
from accounts.models import Invitation
from editorial.models import LearningUnitVersion
from editorial.services import CHECKS, publish, withdraw, replacement_draft
from .models import QuizAttempt
import io


class QuizTests(AccessCase):
    def setUp(self):
        super().setUp()
        call_command("seed_demo", stdout=io.StringIO())
        self.version = LearningUnitVersion.objects.get(unit__key="demo-cell-comparison")
        self.reviewer = get_user_model().objects.create_user("quiz-reviewer", is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="publish_learningunitversion"))
        self.review(self.version)
        self.sign_in()

    def review(self, version):
        for field in CHECKS:
            setattr(version, field, True)
        version.source_reference = "Automated fixture reference"
        version.review_notes = "Fixture only, not human review evidence."
        version.save()
        publish(version.pk, self.reviewer)

    def body(self, version=None, wrong=False):
        version = version or self.version
        return {"version": version.pk, "submission_id": str(uuid.uuid4()), "answers": [
            {"question_id": q.pk, "choice": next(c for c in "abcd" if c != q.correct_choice) if wrong else q.correct_choice}
            for q in version.questions.all()]}

    def submit(self, body=None):
        return self.client.post("/api/v1/attempts/", body or self.body(), format="json")

    def test_quiz_and_feed_never_expose_keys_before_submission(self):
        response = self.client.get(f"/api/v1/units/{self.version.pk}/quiz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["questions"]), 3)
        for q in response.data["questions"]:
            self.assertEqual(set(q), {"id", "position", "prompt", "choices"})
            self.assertEqual(set(q["choices"]), set("abcd"))
        self.assertEqual(QuizAttempt.objects.count(), 0)
        self.assertNotIn("questions", self.client.get(f"/api/v1/units/{self.version.pk}/").data)
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_server_scores_and_returns_explanations_only_after_submit(self):
        body = self.body(wrong=True)
        body["score"] = 3
        response = self.submit(body)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["score"], 0)
        self.assertTrue(response.data["is_first"])
        for result, q in zip(response.data["results"], self.version.questions.all()):
            self.assertEqual(result["correct_choice"], q.correct_choice)
            self.assertEqual(result["explanation"], q.explanation)
        self.assertEqual(self.submit().data["score"], 3)

    def test_invalid_missing_duplicate_and_foreign_answers_do_not_create_attempts(self):
        valid = self.body()
        invalid = []
        for length in [0, 2, 4]:
            body = copy.deepcopy(valid)
            body["answers"] = (body["answers"] * 2)[:length]
            invalid.append(body)
        body = copy.deepcopy(valid)
        body["answers"][1] = body["answers"][0]
        invalid.append(body)
        body = copy.deepcopy(valid)
        body["answers"][0]["question_id"] = 999999
        invalid.append(body)
        body = copy.deepcopy(valid)
        body["answers"][0]["choice"] = "z"
        invalid.append(body)
        for body in invalid:
            self.assertEqual(self.submit(body).status_code, 400)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_identical_retry_with_reordered_answers_counts_once(self):
        body = self.body()
        first = self.submit(body)
        body["answers"].reverse()
        retry = self.submit(body)
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.data, first.data)
        self.assertEqual(QuizAttempt.objects.count(), 1)
        self.assertEqual(self.client.get("/api/v1/progress/").data["total_attempts"], 1)

    def test_conflicting_submission_id_is_rejected(self):
        body = self.body()
        self.submit(body)
        body["answers"][0]["choice"] = next(c for c in "abcd" if c != body["answers"][0]["choice"])
        self.assertEqual(self.submit(body).status_code, 409)
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_repeat_practice_does_not_inflate_first_play_score(self):
        self.assertEqual(self.client.get("/api/v1/progress/").data, {"completed_units": 0, "total_attempts": 0, "first_attempt_percentage": None})
        self.submit(self.body(wrong=True))
        repeat = self.submit()
        self.assertFalse(repeat.data["is_first"])
        self.assertEqual(repeat.data["number"], 2)
        self.assertEqual(self.client.get("/api/v1/progress/").data, {"completed_units": 1, "total_attempts": 2, "first_attempt_percentage": 0.0})
        history = self.client.get("/api/v1/attempts/").data
        self.assertEqual(history["count"], 2)
        self.assertNotIn("results", history["results"][0])

    def test_attempts_and_progress_are_private(self):
        first = self.submit().data
        self.client.credentials()
        Invitation.objects.create(email="other@example.com")
        token = self.link("other@example.com")
        exchange = self.client.post("/api/v1/auth/exchange/", {"token": token}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + exchange.data["credential"])
        self.assertEqual(self.client.get(f"/api/v1/attempts/{first['id']}/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/attempts/").data["count"], 0)
        self.assertEqual(self.client.get("/api/v1/progress/").data["completed_units"], 0)

    def test_all_quiz_routes_require_student_session(self):
        attempt = self.submit().data
        self.client.credentials()
        for path in [f"units/{self.version.pk}/quiz/", "attempts/", f"attempts/{attempt['id']}/", "progress/"]:
            self.assertEqual(self.client.get("/api/v1/" + path).status_code, 401)
        self.assertEqual(self.submit().status_code, 401)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get("/api/v1/progress/").status_code, 401)

    def test_withdrawal_blocks_new_attempt_but_preserves_result_and_retry(self):
        body = self.body()
        result = self.submit(body).data
        withdraw(self.version.pk, self.reviewer)
        self.assertEqual(self.client.get(f"/api/v1/units/{self.version.pk}/quiz/").status_code, 404)
        self.assertEqual(self.submit().status_code, 404)
        self.assertEqual(self.submit(body).data, result)
        self.assertEqual(self.client.get(f"/api/v1/attempts/{result['id']}/").data, result)
        self.assertEqual(QuizAttempt.objects.count(), 1)

    def test_replacement_keeps_completion_and_original_result_snapshot(self):
        original = self.submit().data
        draft = replacement_draft(self.version.pk)
        draft.title = "Updated fixture title"
        self.review(draft)
        repeat = self.submit(self.body(draft)).data
        self.assertEqual(repeat["number"], 2)
        self.assertFalse(repeat["is_first"])
        self.assertEqual(self.client.get("/api/v1/progress/").data["completed_units"], 1)
        self.assertEqual(self.client.get(f"/api/v1/attempts/{original['id']}/").data, original)
        self.assertEqual(self.submit().status_code, 404)

    def test_inactive_exam_hides_quiz_and_rejects_new_submission(self):
        exam = self.version.topic.subject.examination
        exam.is_active = False
        exam.save()
        self.assertEqual(self.client.get(f"/api/v1/units/{self.version.pk}/quiz/").status_code, 404)
        self.assertEqual(self.submit().status_code, 404)

    def test_attempt_constraints_and_supported_edits_are_blocked(self):
        self.submit()
        attempt = QuizAttempt.objects.get()
        with self.assertRaises(ValidationError):
            attempt.save()
        with self.assertRaises(ValidationError):
            attempt.delete()
        values = {field.name: getattr(attempt, field.name) for field in QuizAttempt._meta.fields if field.name not in ["id", "completed_at"]}
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuizAttempt.objects.create(**values)

    def test_database_contention_returns_retryable_response_without_an_attempt(self):
        from unittest.mock import patch
        from django.db import OperationalError
        with patch("learning.views.submit_attempt", side_effect=OperationalError("private database details")):
            response = self.submit()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private database details", str(response.data))
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_admin_attempt_history_has_no_edit_or_delete_actions(self):
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from .admin import QuizAttemptAdmin
        request = RequestFactory().get("/admin/")
        request.user = get_user_model().objects.create_superuser("attempt-admin", password="fixture-only")
        admin = QuizAttemptAdmin(QuizAttempt, AdminSite())
        self.assertFalse(admin.has_add_permission(request))
        self.assertFalse(admin.has_change_permission(request))
        self.assertFalse(admin.has_delete_permission(request))
