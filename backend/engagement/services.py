from zoneinfo import ZoneInfo
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from editorial.models import Card
from editorial.student_api import available_versions
from .models import Like, EngagementEvent

PILOT_ZONE = ZoneInfo("Africa/Lagos")


def available_card(version_id, identity):
    return get_object_or_404(Card.objects.select_related("version__unit", "version__topic__subject__examination", "media"),
                             version_id=version_id, identity=identity, version__in=available_versions())


@transaction.atomic
def set_like(user, version_id, identity, liked):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    card = available_card(version_id, identity)
    row, _ = Like.objects.get_or_create(user=user, unit_id=card.version.unit_id, card_identity=identity)
    if row.is_active != liked:
        row.is_active = liked
        row.save(update_fields=["is_active", "updated_at"])
    return row.is_active


@transaction.atomic
def record_event(user, version_id, identity, kind):
    card = available_card(version_id, identity)
    subject = card.version.topic.subject
    row, created = EngagementEvent.objects.get_or_create(user=user, unit_id=card.version.unit_id,
        card_identity=identity, kind=kind, day=timezone.localdate(timezone=PILOT_ZONE), defaults={
            "version": card.version,
            "context": {"examination": subject.examination.name, "subject": subject.name,
                        "topic": card.version.topic.name, "media_kind": card.media.kind if card.media_id else "text"},
        })
    if kind == "dare_accepted":
        EngagementEvent.objects.get_or_create(user=user, unit_id=card.version.unit_id, card_identity=identity,
            kind="dare_shown", day=row.day, defaults={"version": row.version, "context": row.context})
    return row, created
