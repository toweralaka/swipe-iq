import io
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.db import IntegrityError, OperationalError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from accounts.tests import AccessCase
from accounts.models import Invitation
from editorial.models import LearningUnitVersion
from editorial.services import CHECKS, publish, withdraw, replacement_draft
from learning.models import QuizAttempt
from .models import Like, EngagementEvent
from .reporting import aggregate_report
from .services import PILOT_ZONE


class EngagementTests(AccessCase):
    def setUp(self):
        super().setUp()
        call_command("seed_demo", stdout=io.StringIO())
        self.version = LearningUnitVersion.objects.get(unit__key="demo-cell-comparison")
        self.reviewer = get_user_model().objects.create_user("engagement-reviewer", is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="publish_learningunitversion"))
        self.review(self.version)
        self.card = self.version.cards.get()
        self.sign_in()

    def review(self, version):
        for field in CHECKS:
            setattr(version, field, True)
        version.source_reference = "Checked fixture reference"
        version.review_notes = "Test fixture, not actual educational approval"
        version.save()
        publish(version.pk, self.reviewer)

    def url(self, version=None, identity=None):
        return f"/api/v1/units/{(version or self.version).pk}/cards/{identity or self.card.identity}/like/"

    def event(self, kind="view", version=None, identity=None):
        return self.client.post("/api/v1/engagement/events/", {"version": (version or self.version).pk,
            "card_identity": str(identity or self.card.identity), "kind": kind}, format="json")

    def test_like_and_unlike_are_explicit_persistent_and_idempotent(self):
        self.assertEqual(self.client.get(self.url()).data, {"liked": False})
        for _ in range(3):
            self.assertEqual(self.client.post(self.url(), {"liked": True}, format="json").data, {"liked": True})
        self.assertEqual(Like.objects.count(), 1)
        self.assertTrue(Like.objects.get().is_active)
        self.assertEqual(self.client.get(self.url())["Cache-Control"], "private, no-store")
        for _ in range(3):
            self.assertEqual(self.client.post(self.url(), {"liked": False}, format="json").data, {"liked": False})
        self.assertEqual(Like.objects.count(), 1)
        self.assertFalse(Like.objects.get().is_active)

    def test_like_state_is_private_and_body_cannot_choose_another_user(self):
        self.client.post(self.url(), {"liked": True}, format="json")
        first_user = Like.objects.get().user_id
        self.client.credentials()
        Invitation.objects.create(email="other@example.com")
        token = self.link("other@example.com")
        exchange = self.client.post("/api/v1/auth/exchange/", {"token": token}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + exchange.data["credential"])
        self.assertEqual(self.client.get(self.url()).data, {"liked": False})
        self.client.post(self.url(), {"liked": False, "user": first_user}, format="json")
        self.assertTrue(Like.objects.get(user_id=first_user).is_active)

    def test_likes_survive_replacement_versions_by_stable_card_identity(self):
        self.client.post(self.url(), {"liked": True}, format="json")
        draft = replacement_draft(self.version.pk)
        self.review(draft)
        self.assertEqual(draft.cards.get().identity, self.card.identity)
        self.assertEqual(self.client.get(self.url(draft)).data, {"liked": True})
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.post(self.url(draft), {"liked": False}, format="json")
        self.assertEqual(Like.objects.count(), 1)
        self.assertFalse(Like.objects.get().is_active)

    def test_unavailable_or_mismatched_card_rejects_reads_and_writes(self):
        import uuid
        self.assertEqual(self.client.get(self.url(identity=uuid.uuid4())).status_code, 404)
        other = LearningUnitVersion.objects.exclude(pk=self.version.pk).get()
        self.assertEqual(self.client.get(self.url(other)).status_code, 404)
        self.assertEqual(self.event(version=other).status_code, 404)
        exam = self.version.topic.subject.examination
        exam.is_active = False
        exam.save()
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.assertEqual(self.client.post(self.url(), {"liked": True}, format="json").status_code, 404)
        self.assertEqual(self.event().status_code, 404)
        exam.is_active = True
        exam.save()
        withdraw(self.version.pk, self.reviewer)
        self.assertEqual(self.client.post(self.url(), {"liked": True}, format="json").status_code, 404)
        self.assertEqual(self.event().status_code, 404)
        self.assertEqual(Like.objects.count(), 0)
        self.assertEqual(EngagementEvent.objects.count(), 0)

    def test_invalid_input_and_unsupported_methods_do_not_write(self):
        for data in [{}, {"liked": None}, {"liked": "wrong"}]:
            self.assertEqual(self.client.post(self.url(), data, format="json").status_code, 400)
        for kind in ["made_up", "like", "dare_skipped"]:
            self.assertEqual(self.event(kind).status_code, 400)
        self.assertEqual(self.client.get("/api/v1/engagement/events/").status_code, 405)
        self.assertEqual(Like.objects.count(), 0)
        self.assertEqual(EngagementEvent.objects.count(), 0)

    def test_all_student_engagement_routes_require_candidate_session(self):
        self.client.credentials()
        self.assertEqual(self.client.get(self.url()).status_code, 401)
        self.assertEqual(self.client.post(self.url(), {"liked": True}, format="json").status_code, 401)
        self.assertEqual(self.event().status_code, 401)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.get(self.url()).status_code, 401)
        self.assertEqual(self.event().status_code, 401)

    def test_events_are_deduplicated_per_candidate_card_kind_and_lagos_day(self):
        self.assertEqual(self.event().status_code, 201)
        self.assertEqual(self.event().status_code, 200)
        self.assertEqual(EngagementEvent.objects.count(), 1)
        tomorrow = timezone.localdate(timezone=PILOT_ZONE) + timedelta(days=1)
        with patch("engagement.services.timezone.localdate", return_value=tomorrow):
            self.assertEqual(self.event().status_code, 201)
        self.assertEqual(EngagementEvent.objects.count(), 2)
        for row in EngagementEvent.objects.all():
            self.assertEqual(row.context["media_kind"], "text")
            self.assertEqual(row.context["examination"], "JAMB")

    def test_acceptance_records_exposure_even_if_the_tap_was_quick(self):
        self.assertEqual(self.event("dare_accepted").status_code, 201)
        self.assertEqual(self.event("dare_accepted").status_code, 200)
        self.assertEqual(self.event("dare_shown").status_code, 200)
        self.assertEqual(EngagementEvent.objects.count(), 2)
        self.assertEqual(QuizAttempt.objects.count(), 0)

    def test_lagos_day_boundary_uses_server_time_not_client_day(self):
        instant = datetime(2026, 10, 12, 23, 30, tzinfo=dt_timezone.utc)
        with patch("engagement.services.timezone.now", return_value=instant):
            response = self.event()
        self.assertEqual(response.data["day"], "2026-10-13")

    def test_database_unique_constraints_prevent_duplicate_likes_and_events(self):
        self.client.post(self.url(), {"liked": True}, format="json")
        row = Like.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Like.objects.create(user=row.user, unit=row.unit, card_identity=row.card_identity, is_active=True)
        self.event()
        row = EngagementEvent.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            EngagementEvent.objects.create(user=row.user, unit=row.unit, version=row.version,
                card_identity=row.card_identity, day=row.day, kind=row.kind, context=row.context)

    def test_database_error_is_safe_and_does_not_claim_success(self):
        with patch("engagement.views.set_like", side_effect=OperationalError("private connection detail")):
            response = self.client.post(self.url(), {"liked": True}, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private connection detail", str(response.data))
        self.assertEqual(Like.objects.count(), 0)

    def test_like_does_not_change_random_feed_order(self):
        params = {"subjects": self.version.topic.subject_id, "mix": "a" * 32}
        before = self.client.get("/api/v1/feed/", params).data["results"]
        self.client.post(self.url(), {"liked": True}, format="json")
        self.assertEqual(self.client.get("/api/v1/feed/", params).data["results"], before)

    def test_aggregate_report_counts_without_exporting_accounts_or_secrets(self):
        import uuid
        today = timezone.localdate(timezone=PILOT_ZONE)
        yesterday = today - timedelta(days=1)
        with patch("engagement.services.timezone.localdate", return_value=yesterday):
            self.event()
        self.event()
        self.event("dare_accepted")
        self.client.post(self.url(), {"liked": True}, format="json")
        for _ in range(2):
            self.client.post("/api/v1/attempts/", {"version": self.version.pk, "submission_id": str(uuid.uuid4()),
                "answers": [{"question_id": q.pk, "choice": q.correct_choice} for q in self.version.questions.all()]}, format="json")
        report = aggregate_report()
        self.assertEqual(report["content"][0]["daily_views"], 2)
        self.assertEqual(report["content"][0]["unique_viewers"], 1)
        self.assertEqual(report["content"][0]["viewers_with_active_like"], 1)
        self.assertEqual(report["content"][0]["dare_accepted"], 1)
        self.assertEqual(report["active_likes_as_of_now"][0]["active_likes"], 1)
        self.assertEqual(report["candidates_active_on_multiple_days"], 1)
        self.assertEqual(report["quiz_summary"][0]["attempts"], 2)
        self.assertEqual(report["quiz_summary"][0]["first_attempts"], 1)
        self.assertEqual(report["quiz_summary"][0]["practice_attempts"], 1)
        import json
        raw = json.dumps(report)
        for value in ["student@example.com", "other@example.com", "user_id", "username", "credential", "answers", "correct_choice"]:
            self.assertNotIn(value, raw)
        self.assertEqual(aggregate_report(1)["content"][0]["daily_views"], 1)
        for days in [0, 91]:
            with self.assertRaises(ValueError):
                aggregate_report(days)

    def test_report_download_needs_staff_and_explicit_export_permission(self):
        url = reverse("admin:engagement-export")
        browser = Client()
        self.assertEqual(browser.get(url).status_code, 302)
        browser.force_login(self.reviewer)
        self.assertEqual(browser.get(url).status_code, 403)
        self.reviewer.user_permissions.add(Permission.objects.get(codename="export_engagementevent"))
        response = browser.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(browser.get(url, {"days": "bad"}).status_code, 400)
        self.assertEqual(browser.get(url, {"days": "91"}).status_code, 400)

    def test_admin_report_link_is_visible_only_with_export_permission(self):
        browser = Client()
        self.reviewer.user_permissions.add(Permission.objects.get(codename="view_engagementevent"))
        browser.force_login(self.reviewer)
        url = reverse("admin:engagement_engagementevent_changelist")
        response = browser.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Download 7-day aggregate report")
        self.reviewer.user_permissions.add(Permission.objects.get(codename="export_engagementevent"))
        self.assertContains(browser.get(url), "Download 7-day aggregate report")
