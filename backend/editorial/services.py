from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Card, LearningUnitVersion, MediaAsset, Question

CHECKS = ("accuracy_checked", "syllabus_checked", "humour_checked", "accessibility_checked", "rights_checked", "references_checked")


def require_reviewer(user):
    if not user.is_active or not user.is_staff or not user.has_perm("editorial.publish_learningunitversion"):
        raise PermissionDenied("Reviewer permission is required.")


@transaction.atomic
def publish(version_id, reviewer):
    require_reviewer(reviewer)
    version = LearningUnitVersion.objects.select_for_update().get(pk=version_id)
    if version.status != "draft":
        raise ValidationError("Only drafts can be published.")
    version.full_clean()
    if not all(getattr(version, field) for field in CHECKS):
        raise ValidationError("Complete all six human-review confirmations before publication.")
    if not version.syllabus_reference or not version.source_reference.strip() or not version.review_notes.strip():
        raise ValidationError("Record syllabus, verified reference, and human review notes.")
    cards = list(version.cards.all())
    questions = list(version.questions.all())
    if len(cards) != 1 or cards[0].position != 1:
        raise ValidationError("A post needs exactly one content card, numbered 1. Carousels are future work.")
    if len(questions) not in [0, 3] or (questions and [q.position for q in questions] != [1, 2, 3]):
        raise ValidationError("A post can have no questions or exactly three questions numbered 1, 2, 3.")
    for child in cards + questions:
        child.full_clean()
    for card in cards:
        if card.media_id:
            media = MediaAsset.objects.select_for_update().get(pk=card.media_id)
            media.full_clean()
            if not media.metadata_checked:
                raise ValidationError("Verify attached media metadata, playback, captions, and rights first.")
    version.status = "published"
    version.reviewer = reviewer
    version.reviewed_at = version.published_at = timezone.now()
    version._transition = True
    version.save()
    return version


@transaction.atomic
def withdraw(version_id, reviewer):
    require_reviewer(reviewer)
    version = LearningUnitVersion.objects.select_for_update().get(pk=version_id)
    if version.status != "published":
        raise ValidationError("Only published versions can be withdrawn.")
    version.status = "withdrawn"
    version.withdrawn_at = timezone.now()
    version._transition = True
    version.save(update_fields=["status", "withdrawn_at"])
    return version


@transaction.atomic
def replacement_draft(version_id):
    source = LearningUnitVersion.objects.select_for_update().get(pk=version_id)
    # Serialize version allocation by locking the stable unit as well.
    type(source.unit).objects.select_for_update().get(pk=source.unit_id)
    latest = source.unit.versions.order_by("-number").first()
    draft = LearningUnitVersion.objects.create(
        unit=source.unit, number=latest.number + 1, title=source.title, topic=source.topic,
        objective=source.objective, syllabus_reference=source.syllabus_reference,
        source_reference=source.source_reference, ai_provenance=source.ai_provenance,
    )
    for card in source.cards.all():
        Card.objects.create(version=draft, identity=card.identity, position=card.position, text=card.text, media=card.media)
    for question in source.questions.all():
        data = {f: getattr(question, f) for f in ["position", "prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation"]}
        Question.objects.create(version=draft, **data)
    return draft
