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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique request number. Use this when checking a problem with this request.")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, help_text="Staff member who requested this draft. Saved automatically.")
    topic = models.ForeignKey("editorial.Topic", on_delete=models.PROTECT, help_text="Choose the topic this post teaches. Its subject and examination are taken from this topic.")
    context = models.JSONField(help_text="Saved examination, subject, and topic details from when the request was created.")
    objective = models.TextField(max_length=1000, help_text="State one thing the reader should understand. Example: Explain how osmosis moves water across a membrane.")
    brief = models.TextField(max_length=2000, help_text="Describe the funny post you want. Example: Compare osmosis to guests moving into a less crowded party. Keep the science accurate.")
    syllabus_reference = models.URLField(help_text="Paste the official syllabus page or PDF link. This link is saved as a reference; the app does not open it for you.")
    syllabus_excerpt = models.TextField(max_length=10000, help_text="Paste the relevant syllabus topic or objective. Include enough text to show what the post must cover.")
    source_reference = models.TextField(max_length=2000, help_text="Name the teaching source you checked, with its page or section and a link if available. Example: Biology textbook, osmosis section, page 42.")
    source_excerpt = models.TextField(max_length=10000, help_text="Paste the checked explanation the AI should use. Links are not downloaded automatically. Do not include student names or personal details.")
    format = models.CharField(max_length=10, default="text", choices=[("text", "Text")], help_text="Choose the post format. Only text is available now; images, memes, and video need later stages.")
    include_questions = models.BooleanField(default=False, help_text="Tick to request exactly three multiple-choice questions with explanations. Leave unticked for a post without a quiz. All questions need human review.")
    fingerprint = models.CharField(max_length=64, help_text="Saved check used to recognise repeated submissions of the same request.")
    model_name = models.CharField(max_length=100, help_text="AI model chosen for this request. Saved requests keep this model even if backend settings change.")
    prompt_version = models.CharField(max_length=40, default="text-v1", help_text="Version of the instructions used to generate this draft.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED, help_text="Queued: waiting for the worker. Generating: the worker is making the request. Response saved: waiting for import. Draft ready: ready for human review, not published. Failed: read the message. Needs checking: inspect the result and provider activity before making another request.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this request was saved.")
    started_at = models.DateTimeField(null=True, help_text="When the worker started processing this request. Empty means it has not started.")
    finished_at = models.DateTimeField(null=True, help_text="When processing ended or stopped for checking. This does not mean the draft was published.")
    provider_response_id = models.CharField(max_length=200, blank=True, help_text="Response number from OpenAI, if saved. Use it to check provider activity after a problem.")
    usage = models.JSONField(default=dict, help_text="Token-use details reported by OpenAI. These are not a confirmed price or bill.")
    output = models.JSONField(default=dict, help_text="Saved AI response, including draft text, any questions, and verification notes. A human must check its accuracy.")
    message = models.TextField(blank=True, help_text="Latest result or problem and what to do next. Refresh this page to see saved progress; refreshing does not generate again.")
    result_version = models.OneToOneField("editorial.LearningUnitVersion", null=True, blank=True, on_delete=models.PROTECT, help_text="New draft created from this request. Open it to edit, review, and explicitly publish. Empty means no draft has been created.")

    def __str__(self):
        return f"{self.topic}: {self.get_status_display()}"

    class Meta:
        verbose_name = "content generation request"
        verbose_name_plural = "Content generation requests"
        ordering = ["created_at", "pk"]
        permissions = [("generate_content", "Can request AI content drafts")]
