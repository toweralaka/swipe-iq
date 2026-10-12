import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models, transaction
from django.urls import reverse


class PrivateMediaStorage(FileSystemStorage):
    def url(self, name):
        return reverse("editorial-media", args=[name.split("/")[1]])


def media_path(instance, filename):
    return f"editorial/{instance.pk}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


class EditorialQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Use instance saves or editorial services; bulk updates bypass review rules.")

    def delete(self):
        raise ValidationError("Bulk deletion is disabled for editorial records.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Use validated instance saves.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Use validated instance saves.")


class ValidatedModel(models.Model):
    objects = EditorialQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Examination(ValidatedModel):
    code = models.SlugField(unique=True, help_text="Stable identifier, e.g. jamb or ssce.")
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False, help_text="Only activate when content and student access are ready.")

    def __str__(self):
        return self.name


class Subject(ValidatedModel):
    examination = models.ForeignKey(Examination, related_name="subjects", on_delete=models.PROTECT)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["examination", "name"], name="unique_exam_subject")]

    def clean(self):
        super().clean()
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.examination_id != self.examination_id and Topic.objects.filter(subject_id=self.pk, learningunitversion__status__in=["published", "withdrawn"]).exists():
                raise ValidationError("Cannot reassign the examination of published history. Create a separate subject.")

    def __str__(self):
        return f"{self.examination} {self.name}"


class Topic(ValidatedModel):
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    name = models.CharField(max_length=150)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["subject", "name"], name="unique_subject_topic")]

    def clean(self):
        super().clean()
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.subject_id != self.subject_id and LearningUnitVersion.objects.filter(topic_id=self.pk, status__in=["published", "withdrawn"]).exists():
                raise ValidationError("Cannot reassign the subject of published history. Create a separate topic.")

    def __str__(self):
        return f"{self.subject}: {self.name}"


class LearningUnit(ValidatedModel):
    """Stable identity shared by revisions and future likes."""
    key = models.SlugField(unique=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.key


class LearningUnitVersion(ValidatedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        WITHDRAWN = "withdrawn", "Withdrawn"

    unit = models.ForeignKey(LearningUnit, related_name="versions", on_delete=models.PROTECT)
    number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT)
    objective = models.TextField()
    syllabus_reference = models.URLField(blank=True)
    source_reference = models.TextField(blank=True, help_text="Checked textbook/page or verified source URL.")
    ai_provenance = models.TextField(blank=True, help_text="Tool/model/date/prompt notes; never paste private data.")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT, editable=False)
    accuracy_checked = models.BooleanField(default=False)
    syllabus_checked = models.BooleanField(default=False)
    humour_checked = models.BooleanField(default=False)
    accessibility_checked = models.BooleanField(default=False)
    rights_checked = models.BooleanField(default=False)
    references_checked = models.BooleanField(default=False)
    review_notes = models.TextField(blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, editable=False,
                                 related_name="reviewed_units", on_delete=models.PROTECT)
    reviewed_at = models.DateTimeField(null=True, editable=False)
    published_at = models.DateTimeField(null=True, editable=False)
    withdrawn_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["unit", "number"], name="unique_unit_version")]
        permissions = [("publish_learningunitversion", "Can review, publish, and withdraw learning units")]
        ordering = ["unit_id", "number"]

    def __str__(self):
        return f"{self.title} (v{self.number}, {self.status})"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            old = type(self).objects.select_for_update().filter(pk=self.pk).first() if self.pk else None
            if old and old.status != self.Status.DRAFT and not getattr(self, "_transition", False):
                raise ValidationError("Published/withdrawn versions are immutable. Create a replacement draft.")
            if ((old and old.status != self.status) or (not old and self.status != self.Status.DRAFT)) and not getattr(self, "_transition", False):
                raise ValidationError("Use the publication/withdrawal workflow.")
            try:
                return super().save(*args, **kwargs)
            finally:
                self._transition = False

    def delete(self, *args, **kwargs):
        raise ValidationError("Retain version history; withdraw instead of deleting.")


class MediaAsset(ValidatedModel):
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"
        VIDEO = "video", "Video"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    file = models.FileField(upload_to=media_path, storage=PrivateMediaStorage())
    byte_size = models.PositiveIntegerField(default=0, editable=False)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    height_pixels = models.PositiveIntegerField(null=True, blank=True)
    alt_text = models.CharField(max_length=500, blank=True)
    transcript = models.TextField(blank=True)
    captions_vtt = models.TextField(blank=True, help_text="Video: paste checked WEBVTT captions.")
    attribution = models.TextField(help_text="Creator, source, licence/permission; identify original work.")
    metadata_checked = models.BooleanField(default=False, help_text="Human verified duration, dimensions, format/playback, captions and rights.")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.kind}: {Path(self.file.name).name}"

    def clean(self):
        super().clean()
        if not self.file:
            return
        limits = {"image": 250_000, "audio": 1_000_000, "video": 5_000_000}
        if self.kind not in limits:
            return
        try:
            self.byte_size = self.file.size
        except OSError as error:
            raise ValidationError({"file": "Stored file is missing or inaccessible; upload a replacement."}) from error
        if self.byte_size > limits[self.kind] or self.byte_size == 0:
            raise ValidationError({"file": f"File must be nonempty and no larger than {limits[self.kind]} bytes."})
        try:
            self.file.open("rb")
        except OSError as error:
            raise ValidationError({"file": "Cannot read media; upload a replacement."}) from error
        try:
            header = self.file.read(16)
        finally:
            if self.file._committed:
                self.file.close()
            else:
                self.file.seek(0)
        suffix = Path(self.file.name).suffix.lower()
        valid = {
            "image": (suffix == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n")) or (suffix in [".jpg", ".jpeg"] and header.startswith(b"\xff\xd8\xff")),
            "audio": (suffix == ".wav" and header[:4] == b"RIFF" and header[8:12] == b"WAVE") or (suffix == ".mp3" and (header.startswith(b"ID3") or (len(header) > 1 and header[0] == 255 and header[1] & 224 == 224))),
            "video": suffix == ".mp4" and header[4:8] == b"ftyp",
        }
        if not valid[self.kind]:
            raise ValidationError({"file": "Unsupported file signature/extension. Use PNG/JPEG, MP3/WAV, or MP4."})
        if self.kind == "image" and not self.alt_text.strip():
            raise ValidationError({"alt_text": "Describe the educational image."})
        if self.kind in ["audio", "video"]:
            limit = 90 if self.kind == "audio" else 60
            if not self.duration_seconds or self.duration_seconds > limit:
                raise ValidationError({"duration_seconds": f"Enter verified duration, 1–{limit} seconds."})
            if not self.transcript.strip():
                raise ValidationError({"transcript": "Provide a transcript/text alternative."})
        if self.kind == "video":
            if not self.height_pixels or self.height_pixels > 480:
                raise ValidationError({"height_pixels": "Enter verified video height, 1–480 pixels."})
            if not self.captions_vtt.strip().startswith("WEBVTT"):
                raise ValidationError({"captions_vtt": "Provide checked WEBVTT captions."})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            type(self).objects.select_for_update().filter(pk=self.pk).first()
            if type(self).objects.filter(pk=self.pk, cards__version__status__in=["published", "withdrawn"]).exists():
                raise ValidationError("Assets used by published history are immutable; upload a replacement.")
            return super().save(*args, **kwargs)


class DraftChild(ValidatedModel):
    version = models.ForeignKey(LearningUnitVersion, on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        with transaction.atomic():
            ids = [self.version_id]
            if self.pk:
                previous = type(self).objects.filter(pk=self.pk).values_list("version_id", flat=True).first()
                if previous:
                    ids.append(previous)
            versions = list(LearningUnitVersion.objects.select_for_update().filter(pk__in=ids))
            if any(v.status != "draft" for v in versions):
                raise ValidationError("Published/withdrawn content is immutable; create a replacement draft.")
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            version = LearningUnitVersion.objects.select_for_update().get(pk=self.version_id)
            if version.status != "draft":
                raise ValidationError("Published/withdrawn content cannot be deleted.")
            return super().delete(*args, **kwargs)


class Card(DraftChild):
    version = models.ForeignKey(LearningUnitVersion, related_name="cards", on_delete=models.PROTECT)
    identity = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Stable feed identity retained in replacement versions.")
    position = models.PositiveSmallIntegerField(default=1)
    text = models.TextField(help_text="Required explanation/summary; works without loading media.")
    media = models.ForeignKey(MediaAsset, null=True, blank=True, related_name="cards", on_delete=models.PROTECT)

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["version", "position"], name="unique_card_position"),
                       models.UniqueConstraint(fields=["version", "identity"], name="unique_version_card_identity")]

    def __str__(self):
        return f"Card {self.position}: {self.text[:60]}"


class Question(DraftChild):
    version = models.ForeignKey(LearningUnitVersion, related_name="questions", on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField(default=1)
    prompt = models.TextField()
    choice_a = models.CharField(max_length=300)
    choice_b = models.CharField(max_length=300)
    choice_c = models.CharField(max_length=300)
    choice_d = models.CharField(max_length=300)
    correct_choice = models.CharField(max_length=1, choices=[(c, c.upper()) for c in "abcd"])
    explanation = models.TextField()

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["version", "position"], name="unique_question_position")]

    def clean(self):
        super().clean()
        choices = [getattr(self, "choice_" + c).strip().casefold() for c in "abcd"]
        if len(set(choices)) != 4 or not all(choices):
            raise ValidationError("Provide four distinct nonempty choices.")

    def __str__(self):
        return f"Q{self.position}: {self.prompt[:60]}"
