import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    unit = models.ForeignKey("editorial.LearningUnit", on_delete=models.PROTECT)
    version = models.ForeignKey("editorial.LearningUnitVersion", on_delete=models.PROTECT)
    submission_id = models.UUIDField()
    number = models.PositiveIntegerField()
    answers = models.JSONField()
    results = models.JSONField()
    context = models.JSONField()
    score = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField(default=3)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at", "-pk"]
        constraints = [
            models.UniqueConstraint(fields=["user", "submission_id"], name="unique_user_submission"),
            models.UniqueConstraint(fields=["user", "unit", "number"], name="unique_user_unit_attempt"),
            models.CheckConstraint(condition=models.Q(number__gte=1), name="attempt_number_positive"),
            models.CheckConstraint(condition=models.Q(total=3, score__lte=3), name="attempt_score_valid"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Completed attempts cannot be edited.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Keep completed attempts as learning history.")
