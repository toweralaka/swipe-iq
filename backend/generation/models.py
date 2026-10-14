import uuid
from django.conf import settings
from django.db import models


class DailyQuota(models.Model):
    day = models.DateField(primary_key=True)
    used = models.PositiveIntegerField(default=0)


class GenerationJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Generating"
        RECEIVED = "received", "Response saved"
        READY = "ready", "Draft ready"
        FAILED = "failed", "Failed"
        CHECK = "needs_checking", "Needs checking"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    topic = models.ForeignKey("editorial.Topic", on_delete=models.PROTECT)
    context = models.JSONField()
    objective = models.TextField(max_length=1000)
    brief = models.TextField(max_length=2000)
    syllabus_reference = models.URLField()
    syllabus_excerpt = models.TextField(max_length=10000)
    source_reference = models.TextField(max_length=2000)
    source_excerpt = models.TextField(max_length=10000)
    format = models.CharField(max_length=10, default="text", choices=[("text", "Text")])
    include_questions = models.BooleanField(default=False)
    fingerprint = models.CharField(max_length=64)
    model_name = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=40, default="text-v1")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    provider_response_id = models.CharField(max_length=200, blank=True)
    usage = models.JSONField(default=dict)
    output = models.JSONField(default=dict)
    message = models.TextField(blank=True)
    result_version = models.OneToOneField("editorial.LearningUnitVersion", null=True, blank=True, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.topic}: {self.get_status_display()}"

    class Meta:
        verbose_name = "content generation request"
        verbose_name_plural = "Content generation requests"
        ordering = ["created_at", "pk"]
        permissions = [("generate_content", "Can request AI content drafts")]
