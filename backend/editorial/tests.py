import io
import tempfile
import wave
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Card, LearningUnit, LearningUnitVersion, MediaAsset, Question
from .services import CHECKS, publish, replacement_draft, withdraw


class EditorialTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.temp.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.reviewer = get_user_model().objects.create_user("reviewer", is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="publish_learningunitversion"))
        call_command("seed_demo", stdout=io.StringIO())
        self.version = LearningUnitVersion.objects.get(unit__key="demo-cell-comparison", number=1)

    def ready(self):
        for check in CHECKS:
            setattr(self.version, check, True)
        self.version.source_reference = "Reviewer-checked textbook, chapter/page (test fixture)."
        self.version.review_notes = "Reviewed for this automated workflow fixture, not real educational approval."
        self.version.save()

    def asset(self, kind="audio", **overrides):
        stream = io.BytesIO()
        with wave.open(stream, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(8000)
            wav.writeframes(b"\x00\x00" * 8000)
        data = dict(kind=kind, file=SimpleUploadedFile("test.wav", stream.getvalue()),
                    duration_seconds=1, transcript="Test narration.", attribution="Original test fixture.", metadata_checked=True)
        data.update(overrides)
        return MediaAsset.objects.create(**data)

    def test_seed_is_repeatable_and_preserves_edits(self):
        self.version.title = "Editor changed this"
        self.version.save()
        call_command("seed_demo", stdout=io.StringIO())
        self.assertEqual(LearningUnitVersion.objects.count(), 2)
        self.assertEqual(Card.objects.count(), 2)
        self.assertEqual(Question.objects.count(), 6)
        self.version.refresh_from_db()
        self.assertEqual(self.version.title, "Editor changed this")
        self.assertEqual(self.version.status, "draft")
        self.assertFalse(LearningUnitVersion.objects.exclude(status="draft").exists())

    def test_incomplete_review_cannot_publish(self):
        with self.assertRaises(ValidationError):
            publish(self.version.pk, self.reviewer)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, "draft")

    def test_each_review_confirmation_is_required(self):
        self.ready()
        for check in CHECKS:
            with self.subTest(check=check):
                setattr(self.version, check, False)
                self.version.save()
                with self.assertRaises(ValidationError):
                    publish(self.version.pk, self.reviewer)
                setattr(self.version, check, True)

    def test_missing_question_blocks_publication(self):
        self.ready()
        self.version.questions.first().delete()
        with self.assertRaises(ValidationError):
            publish(self.version.pk, self.reviewer)

    def test_review_notes_and_reference_required(self):
        self.ready()
        self.version.source_reference = ""
        self.version.save()
        with self.assertRaises(ValidationError):
            publish(self.version.pk, self.reviewer)

    def test_permissions_required_even_for_staff(self):
        self.ready()
        user = get_user_model().objects.create_user("editor", is_staff=True)
        with self.assertRaises(PermissionDenied):
            publish(self.version.pk, user)

    def test_publish_freezes_parent_children_and_bulk_paths(self):
        self.ready()
        published = publish(self.version.pk, self.reviewer)
        self.assertEqual(published.reviewer, self.reviewer)
        self.assertIsNotNone(published.published_at)
        published.title = "Tampered"
        with self.assertRaises(ValidationError):
            published.save()
        card = published.cards.first()
        card.text = "Tampered"
        with self.assertRaises(ValidationError):
            card.save()
        with self.assertRaises(ValidationError):
            card.delete()
        question = published.questions.first()
        question.explanation = "Tampered"
        with self.assertRaises(ValidationError):
            question.save()
        with self.assertRaises(ValidationError):
            published.delete()
        with self.assertRaises(ValidationError):
            published.cards.update(text="Tampered")
        with self.assertRaises(ValidationError):
            published.questions.all().delete()

    def test_direct_status_change_cannot_bypass_review(self):
        self.version.status = "published"
        with self.assertRaises(ValidationError):
            self.version.save()

    def test_replacement_retains_identity_resets_review_and_withdraw_preserves_history(self):
        self.ready()
        published = publish(self.version.pk, self.reviewer)
        draft = replacement_draft(published.pk)
        self.assertEqual(draft.number, 2)
        self.assertEqual(draft.status, "draft")
        self.assertTrue(all(not getattr(draft, field) for field in CHECKS))
        self.assertIsNone(draft.reviewer)
        self.assertEqual(list(draft.cards.values_list("identity", flat=True)), list(published.cards.values_list("identity", flat=True)))
        self.assertEqual(draft.questions.count(), 3)
        withdrawn = withdraw(published.pk, self.reviewer)
        self.assertEqual(withdrawn.status, "withdrawn")
        self.assertIsNotNone(withdrawn.withdrawn_at)
        self.assertEqual(withdrawn.cards.count(), 1)
        with self.assertRaises(ValidationError):
            publish(withdrawn.pk, self.reviewer)

    def test_audio_limits_and_transcript_validation(self):
        for override in [{"duration_seconds": 91}, {"transcript": ""}, {"file": SimpleUploadedFile("bad.wav", b"not audio")}, {"file": SimpleUploadedFile("large.wav", b"RIFF0000WAVE" + b"0" * 1_000_000)}]:
            with self.subTest(fields=list(override)), self.assertRaises(ValidationError):
                self.asset(**override)

    def test_image_requires_description_and_valid_signature(self):
        for override in [dict(file=SimpleUploadedFile("fake.png", b"bad"), alt_text="diagram"), dict(file=SimpleUploadedFile("tiny.png", b"\x89PNG\r\n\x1a\n"), alt_text="")]:
            with self.subTest(fields=list(override)), self.assertRaises(ValidationError):
                self.asset(kind="image", **override)

    def test_video_requires_captions_and_small_verified_dimensions(self):
        for override in [dict(height_pixels=720, captions_vtt="WEBVTT\n"), dict(height_pixels=480, captions_vtt="")]:
            with self.subTest(fields=override), self.assertRaises(ValidationError):
                self.asset(kind="video", file=SimpleUploadedFile("test.mp4", b"0000ftypisom0000"), **override)

    def test_media_review_required_and_published_assets_cannot_change(self):
        self.ready()
        media = self.asset(metadata_checked=False)
        card = self.version.cards.first()
        card.media = media
        card.save()
        with self.assertRaises(ValidationError):
            publish(self.version.pk, self.reviewer)
        media.metadata_checked = True
        media.save()
        published = publish(self.version.pk, self.reviewer)
        media.transcript = "Changed"
        with self.assertRaises(ValidationError):
            media.save()
        draft = replacement_draft(published.pk)
        # Reusing an immutable reviewed asset is valid; editing it is not.
        for check in CHECKS:
            setattr(draft, check, True)
        draft.review_notes = "Rechecked replacement fixture."
        draft.save()
        self.assertEqual(publish(draft.pk, self.reviewer).status, "published")

    def test_media_is_staff_permission_protected(self):
        media = self.asset()
        url = reverse("editorial-media", args=[media.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        student = get_user_model().objects.create_user("student")
        self.client.force_login(student)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="view_mediaasset"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        response.close()
        self.assertEqual(self.client.get("/private-media/" + media.file.name).status_code, 404)

    def test_admin_sets_author_and_preserves_it_on_edit_despite_posted_author(self):
        admin_user = get_user_model().objects.create_superuser("author-admin", "author@example.com", "test-only-password")
        other = get_user_model().objects.create_user("other-author")
        self.client.force_login(admin_user)
        add_url = reverse("admin:editorial_learningunit_add")
        self.assertNotIn("author", self.client.get(add_url).context["adminform"].form.fields)
        response = self.client.post(add_url, {"key": "admin-authored-fixture", "author": other.pk, "_save": "Save"})
        self.assertEqual(response.status_code, 302)
        unit = LearningUnit.objects.get(key="admin-authored-fixture")
        self.assertEqual(unit.author_id, admin_user.pk)
        self.client.force_login(get_user_model().objects.create_superuser("editing-admin", "editing@example.com", "test-only-password"))
        change_url = reverse("admin:editorial_learningunit_change", args=[unit.pk])
        self.assertNotIn("author", self.client.get(change_url).context["adminform"].form.fields)
        response = self.client.post(change_url, {"key": "admin-authored-renamed", "author": other.pk, "_save": "Save"})
        self.assertEqual(response.status_code, 302)
        unit.refresh_from_db()
        self.assertEqual(unit.author_id, admin_user.pk)

    def test_admin_rejects_student_and_readonly_history(self):
        student = get_user_model().objects.create_user("student")
        self.client.force_login(student)
        url = reverse("admin:editorial_learningunitversion_changelist")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.ready()
        published = publish(self.version.pk, self.reviewer)
        admin_user = get_user_model().objects.create_superuser("admin", "admin@example.com", "test-only-password")
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:editorial_learningunitversion_change", args=[published.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_change_permission"])
        response = self.client.post(reverse("admin:editorial_learningunitversion_change", args=[published.pk]), {"title": "Tampered"})
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:editorial_mediaasset_add"))
        self.assertEqual(response.status_code, 200)

    def test_admin_actions_publish_copy_and_withdraw(self):
        self.ready()
        admin_user = get_user_model().objects.create_superuser("actions-admin", "actions@example.com", "test-only-password")
        self.client.force_login(admin_user)
        url = reverse("admin:editorial_learningunitversion_changelist")
        for action in ["publish_selected", "copy_to_draft", "withdraw_selected"]:
            response = self.client.post(url, {"action": action, "_selected_action": [self.version.pk], "index": "0"})
            self.assertEqual(response.status_code, 302)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, "withdrawn")
        self.assertEqual(self.version.unit.versions.count(), 2)
        self.assertEqual(self.version.unit.versions.get(number=2).status, "draft")

    def test_admin_failed_publication_shows_message_and_preserves_draft(self):
        admin_user = get_user_model().objects.create_superuser("failure-admin", "failure@example.com", "test-only-password")
        self.client.force_login(admin_user)
        response = self.client.post(reverse("admin:editorial_learningunitversion_changelist"),
            {"action": "publish_selected", "_selected_action": [self.version.pk]}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Complete all six human-review confirmations")
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, "draft")

    def test_missing_stored_file_blocks_publication_with_validation_error(self):
        self.ready()
        media = self.asset()
        card = self.version.cards.first()
        card.media = media
        card.save()
        Path(media.file.path).unlink()
        with self.assertRaises(ValidationError):
            publish(self.version.pk, self.reviewer)

    def test_all_media_types_can_be_attached_to_draft_cards(self):
        # Signature fixtures test validation plumbing, not full decodability/playback.
        image = self.asset(kind="image", file=SimpleUploadedFile("fixture.png", b"\x89PNG\r\n\x1a\n"), alt_text="Fixture label")
        audio = self.asset()
        video = self.asset(kind="video", file=SimpleUploadedFile("fixture.mp4", b"0000ftypisom0000"), height_pixels=480, captions_vtt="WEBVTT\n\n00:00.000 --> 00:01.000\nFixture\n")
        version = LearningUnitVersion.objects.get(unit__key="demo-cell-media")
        for asset in [image, audio, video]:
            card = version.cards.get()
            card.media = asset
            card.save()
            card.refresh_from_db()
            self.assertEqual(card.media.kind, asset.kind)
            self.assertEqual(version.cards.count(), 1)

    def test_admin_upload_records_uploader_size_and_private_url(self):
        admin_user = get_user_model().objects.create_superuser("upload-admin", "upload@example.com", "test-only-password")
        self.client.force_login(admin_user)
        fixture = self.asset()
        with fixture.file.open("rb") as source:
            upload = SimpleUploadedFile("narration.wav", source.read(), content_type="audio/wav")
        response = self.client.post(reverse("admin:editorial_mediaasset_add"), {
            "kind": "audio", "file": upload, "duration_seconds": "1",
            "transcript": "A checked narration fixture.", "attribution": "Original test fixture.",
            "metadata_checked": "on", "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        asset = MediaAsset.objects.get(uploaded_by=admin_user)
        self.assertGreater(asset.byte_size, 0)
        self.assertEqual(asset.file.url, reverse("editorial-media", args=[asset.pk]))

    def test_seed_uses_official_jamb_mapping(self):
        from .syllabus import CELL_OBJECTIVE, CELL_TOPIC, JAMB_BIOLOGY_URL
        self.assertEqual(self.version.objective, CELL_OBJECTIVE)
        self.assertEqual(self.version.topic.name, CELL_TOPIC)
        self.assertEqual(self.version.syllabus_reference, JAMB_BIOLOGY_URL)
        self.assertFalse(self.version.syllabus_checked)

    def test_legacy_alignment_changes_mapping_not_content(self):
        from .models import Topic
        from .syllabus import CELL_OBJECTIVE, CELL_TOPIC, LEGACY_OBJECTIVE, LEGACY_TOPIC
        old_topic = Topic.objects.create(subject=self.version.topic.subject, name=LEGACY_TOPIC)
        self.version.topic = old_topic
        self.version.objective = LEGACY_OBJECTIVE
        self.version.save()
        texts = list(self.version.cards.values_list("text", flat=True))
        call_command("seed_demo", align_syllabus=True, stdout=io.StringIO())
        self.version.refresh_from_db()
        self.assertEqual(self.version.objective, CELL_OBJECTIVE)
        self.assertEqual(self.version.topic.name, CELL_TOPIC)
        self.assertEqual(list(self.version.cards.values_list("text", flat=True)), texts)
        self.assertEqual(self.version.status, "draft")
        self.assertFalse(self.version.syllabus_checked)

    def test_alignment_preserves_reviewer_edited_mapping(self):
        self.version.objective = "Reviewer chose a different objective"
        self.version.save()
        call_command("seed_demo", align_syllabus=True, stdout=io.StringIO())
        self.version.refresh_from_db()
        self.assertEqual(self.version.objective, "Reviewer chose a different objective")

    def test_five_sample_units_are_complete_unreviewed_drafts(self):
        call_command("seed_sample_content", stdout=io.StringIO())
        samples = LearningUnitVersion.objects.filter(unit__key__startswith="sample-")
        self.assertEqual(samples.count(), 5)
        for version in samples:
            self.assertEqual(version.status, "draft")
            self.assertIsNone(version.reviewer)
            self.assertTrue(all(not getattr(version, field) for field in CHECKS))
            self.assertEqual(version.cards.count(), 1)
            self.assertEqual(version.questions.count(), 3)
            for question in version.questions.all():
                question.full_clean()
            with self.assertRaises(ValidationError):
                publish(version.pk, self.reviewer)

    def test_sample_seed_preserves_editor_changes_and_does_not_duplicate(self):
        call_command("seed_sample_content", stdout=io.StringIO())
        version = LearningUnitVersion.objects.get(unit__key="sample-membrane-bouncer", number=1)
        card = version.cards.first()
        card.text = "Human editor changed the analogy."
        card.save()
        call_command("seed_sample_content", stdout=io.StringIO())
        card.refresh_from_db()
        self.assertEqual(card.text, "Human editor changed the analogy.")
        self.assertEqual(LearningUnitVersion.objects.filter(unit__key__startswith="sample-").count(), 5)

    def test_subjects_are_unique_per_examination_and_exam_is_required(self):
        from .models import Examination, Subject
        jamb = Examination.objects.get(code="jamb")
        ssce = Examination.objects.create(code="ssce", name="SSCE")
        biology = Subject.objects.create(examination=ssce, name="Biology")
        self.assertEqual(str(biology), "SSCE Biology")
        self.assertEqual(str(self.version.topic.subject), "JAMB Biology")
        self.assertFalse(ssce.is_active)
        with self.assertRaises(ValidationError):
            Subject.objects.create(examination=jamb, name="Biology")
        with self.assertRaises(ValidationError):
            Subject.objects.create(name="Chemistry")

    def test_content_can_be_filtered_by_examination(self):
        from .models import Examination, LearningUnit, Subject, Topic
        ssce = Examination.objects.create(code="ssce", name="SSCE")
        topic = Topic.objects.create(subject=Subject.objects.create(examination=ssce, name="Biology"), name="Cells")
        other = LearningUnitVersion.objects.create(
            unit=LearningUnit.objects.create(key="ssce-cell-fixture"), topic=topic,
            title="SSCE cell fixture", objective="Test exam separation.")
        jamb_content = LearningUnitVersion.objects.filter(topic__subject__examination__code="jamb")
        self.assertEqual(jamb_content.count(), 2)
        self.assertNotIn(other, jamb_content)
        self.assertEqual(LearningUnitVersion.objects.get(topic__subject__examination=ssce), other)

    def test_examination_with_subjects_cannot_be_deleted(self):
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.version.topic.subject.examination.delete()

    def test_published_and_withdrawn_content_cannot_move_to_another_exam(self):
        from .models import Examination, Subject
        self.ready()
        publish(self.version.pk, self.reviewer)
        ssce = Examination.objects.create(code="ssce", name="SSCE")
        other_subject = Subject.objects.create(examination=ssce, name="Biology")
        for status in ["published", "withdrawn"]:
            with self.subTest(status=status):
                self.version.refresh_from_db()
                subject = self.version.topic.subject
                subject.examination = ssce
                with self.assertRaises(ValidationError):
                    subject.save()
                topic = self.version.topic
                topic.subject = other_subject
                with self.assertRaises(ValidationError):
                    topic.save()
                if status == "published":
                    withdraw(self.version.pk, self.reviewer)

    def test_seeds_use_jamb_without_enabling_other_exams(self):
        from .models import Examination, Subject
        ssce = Examination.objects.create(code="ssce", name="SSCE")
        Subject.objects.create(examination=ssce, name="Biology")
        call_command("seed_demo", stdout=io.StringIO())
        call_command("seed_sample_content", stdout=io.StringIO())
        self.assertEqual(LearningUnitVersion.objects.exclude(topic__subject__examination__code="jamb").count(), 0)
        ssce.refresh_from_db()
        self.assertFalse(ssce.is_active)
        self.assertEqual(Examination.objects.count(), 2)

    def test_admin_displays_examination_and_qualified_topic_choices(self):
        admin_user = get_user_model().objects.create_superuser("exam-admin", "exam@example.com", "test-only-password")
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:editorial_learningunitversion_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JAMB")
        response = self.client.get(reverse("admin:editorial_learningunitversion_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JAMB Biology:")
        response = self.client.get(reverse("admin:editorial_subject_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JAMB")

    def test_new_publication_requires_one_card_without_deleting_legacy_draft_cards(self):
        self.ready()
        first = self.version.cards.get()
        extra = Card.objects.create(version=self.version, position=2, text="Legacy extra card")
        with self.assertRaisesMessage(ValidationError, "exactly one content card"):
            publish(self.version.pk, self.reviewer)
        self.assertEqual(self.version.cards.count(), 2)
        extra.delete()
        publish(self.version.pk, self.reviewer)
        self.assertEqual(self.version.cards.get().identity, first.identity)

    def test_seed_rerun_preserves_existing_multi_card_content(self):
        Card.objects.create(version=self.version, position=2, text="Keep this editor content")
        before = list(self.version.cards.values())
        call_command("seed_demo", stdout=io.StringIO())
        self.assertEqual(list(self.version.cards.values()), before)
