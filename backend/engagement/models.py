from django.conf import settings
from django.db import models


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    unit = models.ForeignKey("editorial.LearningUnit", on_delete=models.PROTECT)
    card_identity = models.UUIDField()
    is_active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "unit", "card_identity"], name="one_like_per_user_card")]


class EngagementEvent(models.Model):
    class Kind(models.TextChoices):
        VIEW = "view", "Post visible"
        DARE_SHOWN = "dare_shown", "Dare visible"
        DARE_ACCEPTED = "dare_accepted", "Dare accepted"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    unit = models.ForeignKey("editorial.LearningUnit", on_delete=models.PROTECT)
    version = models.ForeignKey("editorial.LearningUnitVersion", on_delete=models.PROTECT)
    card_identity = models.UUIDField()
    kind = models.CharField(max_length=20, choices=Kind.choices)
    day = models.DateField(db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)
    context = models.JSONField()

    class Meta:
        permissions = [("export_engagementevent", "Can export aggregate engagement reports")]
        constraints = [
            models.UniqueConstraint(fields=["user", "unit", "card_identity", "kind", "day"], name="one_daily_card_event"),
            models.CheckConstraint(condition=models.Q(kind__in=["view", "dare_shown", "dare_accepted"]), name="known_engagement_kind"),
        ]
