import io
import re
from datetime import timedelta
from unittest.mock import patch
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from editorial.models import Examination, LearningUnitVersion, MediaAsset, Subject, Topic
from editorial.services import CHECKS, publish, replacement_draft, withdraw
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from .models import Invitation, LoginToken, RateBucket, StudentSession
from .services import digest


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", LOGIN_LINK_BASE_URL="https://login.example.com/login")
class AccessCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.invitation = Invitation.objects.create(email="student@example.com")

    def link(self, email="student@example.com"):
        response = self.client.post("/api/v1/auth/request-link/", {"email": email}, format="json")
        self.assertEqual(response.status_code, 202)
        return re.search(r"#token=([A-Za-z0-9_-]+)", mail.outbox[-1].body).group(1)

    def sign_in(self):
        raw = self.link()
        response = self.client.post("/api/v1/auth/exchange/", {"token": raw}, format="json")
        self.assertEqual(response.status_code, 200)
        credential = response.data["credential"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + credential)
        return credential


class AccessTests(AccessCase):
    def test_unknown_and_invited_have_identical_generic_responses(self):
        unknown = self.client.post("/api/v1/auth/request-link/", {"email": "unknown@example.com"}, format="json")
        self.assertEqual(len(mail.outbox), 0)
        known = self.client.post("/api/v1/auth/request-link/", {"email": " STUDENT@example.com "}, format="json")
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("token", known.data)

    def test_token_and_session_hashes_and_unusable_password(self):
        raw = self.link()
        self.assertEqual(LoginToken.objects.get().digest, digest(raw))
        token = LoginToken.objects.get()
        self.assertAlmostEqual((token.expires_at-timezone.now()).total_seconds(), 900, delta=5)
        response = self.client.post("/api/v1/auth/exchange/", {"token": raw}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudentSession.objects.get().digest, digest(response.data["credential"]))
        self.assertAlmostEqual((StudentSession.objects.get().expires_at-timezone.now()).total_seconds(), 30*86400, delta=5)
        self.invitation.refresh_from_db()
        self.assertFalse(self.invitation.user.has_usable_password())
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_opening_help_does_not_consume_token(self):
        self.link()
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/exchange/").status_code, 405)
        self.assertIsNone(LoginToken.objects.get().consumed_at)
        self.assertEqual(StudentSession.objects.count(), 0)

    def test_used_expired_invalid_and_malformed_tokens_are_rejected(self):
        raw = self.link()
        self.assertEqual(self.client.post("/api/v1/auth/exchange/", {"token": raw}).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/exchange/", {"token": raw}).status_code, 403)
        expired = self.link()
        LoginToken.objects.filter(digest=digest(expired)).update(expires_at=timezone.now()-timedelta(seconds=1))
        for value in [expired, "x"*43]:
            self.assertEqual(self.client.post("/api/v1/auth/exchange/", {"token": value}).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/auth/exchange/", {"token": "bad"}).status_code, 400)
        self.assertEqual(StudentSession.objects.count(), 1)

    def test_session_required_and_logout_revokes(self):
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        credential = self.sign_in()
        self.assertEqual(self.client.get("/api/v1/auth/me/").data["email"], "student@example.com")
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        self.assertIsNotNone(StudentSession.objects.get(digest=digest(credential)).revoked_at)

    def test_expired_session_and_deactivated_invitation_are_rejected(self):
        self.sign_in()
        StudentSession.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)
        self.client.credentials()
        self.sign_in()
        self.invitation.is_active = False
        self.invitation.save()
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, 401)

    def test_invitation_revoked_between_request_and_exchange(self):
        raw = self.link()
        self.invitation.is_active = False
        self.invitation.save()
        self.assertEqual(self.client.post("/api/v1/auth/exchange/", {"token": raw}).status_code, 403)
        self.assertEqual(StudentSession.objects.count(), 0)

    def test_staff_cookies_and_staff_linked_sessions_do_not_grant_student_access(self):
        staff = get_user_model().objects.create_user("staff", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get("/api/v1/units/").status_code, 401)
        self.invitation.user = staff
        self.invitation.save()
        response = self.client.post("/api/v1/auth/request-link/", {"email": self.invitation.email})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 0)

    def test_address_rate_limit_also_applies_to_unknown_addresses(self):
        for _ in range(3):
            self.assertEqual(self.client.post("/api/v1/auth/request-link/", {"email": "unknown@example.com"}).status_code, 202)
        response = self.client.post("/api/v1/auth/request-link/", {"email": "UNKNOWN@example.com"})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)
        self.assertFalse(RateBucket.objects.filter(key__contains="unknown").exists())

    def test_ip_limit_cannot_be_bypassed_by_changing_address(self):
        for index in range(20):
            self.assertEqual(self.client.post("/api/v1/auth/request-link/", {"email": f"unknown{index}@example.com"}).status_code, 202)
        self.assertEqual(self.client.post("/api/v1/auth/request-link/", {"email": "another@example.com"}).status_code, 429)

    def test_email_failure_returns_generic_response_without_logging_secrets(self):
        with patch("accounts.services.send_mail", side_effect=RuntimeError("private provider body")), self.assertLogs("accounts.views", level="ERROR") as captured:
            response = self.client.post("/api/v1/auth/request-link/", {"email": self.invitation.email})
        self.assertEqual(response.status_code, 202)
        self.assertNotIn("private provider body", str(captured.output))
        self.assertNotIn(self.invitation.email, str(captured.output))
        self.assertEqual(LoginToken.objects.count(), 0)

    def test_app_link_association_is_not_fabricated(self):
        self.assertEqual(self.client.get("/.well-known/assetlinks.json").status_code, 404)
        with override_settings(ANDROID_CERT_FINGERPRINTS=["AA:BB"], ANDROID_PACKAGE="com.swipeiq.mobile"):
            response = self.client.get("/.well-known/assetlinks.json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[0]["target"]["package_name"], "com.swipeiq.mobile")


    def test_linked_account_cannot_be_transferred_by_editing_invitation_email(self):
        from django.core.exceptions import ValidationError
        self.sign_in()
        self.invitation.refresh_from_db()
        self.invitation.email = "another@example.com"
        with self.assertRaises(ValidationError):
            self.invitation.save()


class ContentAccessTests(AccessCase):
    # Reuse setup/helpers only; authentication scenarios live in AccessTests.
    def setUp(self):
        super().setUp()
        call_command("seed_demo", stdout=io.StringIO())
        self.version = LearningUnitVersion.objects.get(unit__key="demo-cell-comparison")
        self.reviewer = get_user_model().objects.create_user("reviewer", is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="publish_learningunitversion"))
        for field in CHECKS:
            setattr(self.version, field, True)
        self.version.source_reference = "Checked test reference"
        self.version.review_notes = "Automated fixture only."
        self.version.save()

    def test_drafts_hidden_then_published_content_has_exam_without_keys_or_reviews(self):
        self.sign_in()
        self.assertEqual(self.client.get("/api/v1/units/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/v1/units/{self.version.pk}/").status_code, 404)
        publish(self.version.pk, self.reviewer)
        response = self.client.get(f"/api/v1/units/{self.version.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["topic"]["subject"]["examination"]["code"], "jamb")
        self.assertEqual(len(response.data["cards"]), 2)
        for key in ["correct_choice", "explanation", "questions", "ai_provenance", "review_notes", "reviewer"]:
            self.assertNotIn(key, response.data)
        self.assertEqual(self.client.get("/api/v1/examinations/").data["results"][0]["code"], "jamb")
        self.assertEqual(self.client.get("/api/v1/subjects/?examination=ssce").data["count"], 0)

    def test_withdrawn_and_inactive_content_hidden_and_latest_published_only(self):
        self.sign_in()
        publish(self.version.pk, self.reviewer)
        draft = replacement_draft(self.version.pk)
        for field in CHECKS:
            setattr(draft, field, True)
        draft.review_notes = "Rechecked fixture"
        draft.save()
        publish(draft.pk, self.reviewer)
        self.assertEqual(self.client.get("/api/v1/units/").data["count"], 1)
        self.assertEqual(self.client.get(f"/api/v1/units/{self.version.pk}/").status_code, 404)
        exam = self.version.topic.subject.examination
        exam.is_active = False
        exam.save()
        self.assertEqual(self.client.get(f"/api/v1/units/{draft.pk}/").status_code, 404)
        exam.is_active = True
        exam.save()
        withdraw(draft.pk, self.reviewer)
        self.assertEqual(self.client.get(f"/api/v1/units/{draft.pk}/").status_code, 404)

    def test_student_cannot_write_content_or_enter_admin(self):
        self.sign_in()
        self.assertEqual(self.client.post("/api/v1/units/", {"title": "tamper"}).status_code, 405)
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_media_requires_auth_and_current_publication(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            asset = MediaAsset.objects.create(kind="image", file=SimpleUploadedFile("fixture.png", b"\x89PNG\r\n\x1a\n"),
                alt_text="Test diagram", attribution="Original fixture", metadata_checked=True)
            card = self.version.cards.first()
            card.media = asset
            card.save()
            url = f"/api/v1/media/{asset.pk}/"
            self.assertEqual(self.client.get(url).status_code, 401)
            self.sign_in()
            self.assertEqual(self.client.get(url).status_code, 404)
            publish(self.version.pk, self.reviewer)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "private, no-store")
            response.close()
            withdraw(self.version.pk, self.reviewer)
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_all_student_routes_require_student_session(self):
        for path in ["examinations/", "subjects/", "topics/", "units/", f"units/{self.version.pk}/"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get("/api/v1/" + path).status_code, 401)

    def test_topics_and_units_can_be_filtered_without_cross_topic_leakage(self):
        self.sign_in()
        publish(self.version.pk, self.reviewer)
        subject = self.version.topic.subject
        other_topic = Topic.objects.create(subject=subject, name="Unpublished topic")
        self.assertEqual(self.client.get(f"/api/v1/units/?topic={other_topic.pk}").data["count"], 0)
        response = self.client.get(f"/api/v1/topics/?subject={subject.pk}")
        self.assertEqual([item["id"] for item in response.data["results"]], [self.version.topic_id])
        self.assertEqual(self.client.get("/api/v1/units/?topic=bad").data["count"], 0)
