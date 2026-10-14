import hashlib
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from editorial.models import LearningUnit, LearningUnitVersion, Card, Question
from .configuration import require_configuration
from .models import DailyQuota, GenerationJob
from .prompts import PROMPT_VERSION
from .provider import generate_text, GenerationFailure, UncertainGeneration
from .validation import validate_output

INPUT_FIELDS = ["topic", "objective", "brief", "syllabus_reference", "syllabus_excerpt", "source_reference", "source_excerpt", "format", "include_questions"]


def require_generator(user):
    if not user.is_active or not user.is_staff or not user.has_perm("generation.generate_content"):
        raise PermissionDenied("AI draft generation permission is required.")


def topic_context(topic):
    subject = topic.subject
    return {"examination": subject.examination.name, "subject": subject.name, "topic": topic.name,
            "examination_id": subject.examination_id, "subject_id": subject.pk}


@transaction.atomic
def enqueue(user, request_id, values):
    require_generator(user)
    normalized = {key: values[key].pk if key == "topic" else values[key] for key in INPUT_FIELDS}
    fingerprint = hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()
    existing = GenerationJob.objects.filter(pk=request_id).first()
    if existing:
        if existing.creator_id != user.pk:
            raise PermissionDenied
        if existing.fingerprint != fingerprint:
            raise ValidationError("This form already created a different request. Open a new generation form.")
        return existing
    require_configuration()
    if values["format"] != "text":
        raise ValidationError("Only text generation is available in AI-1.")
    day = timezone.localdate()
    DailyQuota.objects.get_or_create(day=day)
    if not DailyQuota.objects.filter(day=day, used__lt=settings.AI_DAILY_JOB_LIMIT).update(used=F("used") + 1):
        raise ValidationError("Today's generation limit has been reached. Try again tomorrow.")
    return GenerationJob.objects.create(id=request_id, creator=user, context=topic_context(values["topic"]),
                                         fingerprint=fingerprint, model_name=settings.AI_TEXT_MODEL, prompt_version=PROMPT_VERSION, **values)


@transaction.atomic
def import_draft(job_id):
    job = GenerationJob.objects.select_for_update().get(pk=job_id)
    if job.result_version_id:
        return job.result_version
    if job.status != GenerationJob.Status.RECEIVED:
        raise ValidationError("Only a saved provider result can be imported.")
    if topic_context(job.topic) != job.context:
        raise ValidationError("The topic changed after this request. Keep this result for checking; create a new request for the current topic.")
    output = validate_output(job.output, job.include_questions)
    unit = LearningUnit.objects.create(key="ai-" + job.id.hex, author=job.creator)
    version = LearningUnitVersion.objects.create(unit=unit, number=1, topic=job.topic, title=output["title"],
        objective=job.objective, syllabus_reference=job.syllabus_reference, source_reference=job.source_reference,
        ai_provenance=f"OpenAI draft; job {job.id}; model {job.model_name}; prompt {job.prompt_version}; response {job.provider_response_id}. Human review outstanding. See generation job for source snapshot and verification notes.")
    Card.objects.create(version=version, position=1, text=output["card_text"])
    for position, question in enumerate(output["questions"], 1):
        Question.objects.create(version=version, position=position, prompt=question["prompt"],
            correct_choice=question["correct_choice"], explanation=question["explanation"],
            **{"choice_" + letter: value for letter, value in question["choices"].items()})
    job.result_version = version
    job.status = GenerationJob.Status.READY
    job.message = "Draft created. A human must check it and publish explicitly."
    job.finished_at = timezone.now()
    job.save(update_fields=["result_version", "status", "message", "finished_at"])
    return version


def recover_interrupted():
    # Call only after the worker command obtains the exclusive local process lock.
    return GenerationJob.objects.filter(status=GenerationJob.Status.RUNNING).update(
        status=GenerationJob.Status.CHECK, finished_at=timezone.now(),
        message="The worker stopped before saving a confirmed response. Check provider activity; this request will not be sent again.")


def process_one(provider=None):
    require_configuration()
    job = GenerationJob.objects.filter(status=GenerationJob.Status.RECEIVED).first()
    if job:
        _import_or_mark(job)
        return True
    job = GenerationJob.objects.filter(status=GenerationJob.Status.QUEUED).first()
    if not job:
        return False
    if not GenerationJob.objects.filter(pk=job.pk, status=GenerationJob.Status.QUEUED).update(
            status=GenerationJob.Status.RUNNING, started_at=timezone.now(), message=""):
        return False
    job.refresh_from_db()
    try:
        creator = get_user_model().objects.get(pk=job.creator_id)
        require_generator(creator)
        if topic_context(job.topic) != job.context:
            raise GenerationFailure("The topic changed after the request. Create a new request with the current topic.")
        result = (provider or generate_text)(job)
        # Save before importing, so restart can finish import without another paid call.
        GenerationJob.objects.filter(pk=job.pk, status=GenerationJob.Status.RUNNING).update(
            output=result["output"], provider_response_id=result["response_id"], usage=result["usage"], status=GenerationJob.Status.RECEIVED)
    except UncertainGeneration as problem:
        _mark(job, GenerationJob.Status.CHECK, str(problem))
        return True
    except GenerationFailure as problem:
        GenerationJob.objects.filter(pk=job.pk).update(provider_response_id=problem.response_id, usage=problem.usage)
        _mark(job, GenerationJob.Status.FAILED, str(problem))
        return True
    except PermissionDenied:
        _mark(job, GenerationJob.Status.FAILED, "The requesting staff member no longer has generation permission.")
        return True
    except Exception:
        # Never log raw provider bodies or accidentally requeue a paid request.
        _mark(job, GenerationJob.Status.CHECK, "The response could not be confirmed or saved. Check provider activity; no automatic retry will occur.")
        return True
    _import_or_mark(job)
    return True


def _mark(job, status, message):
    GenerationJob.objects.filter(pk=job.pk).update(status=status, message=message, finished_at=timezone.now())


def _import_or_mark(job):
    try:
        import_draft(job.pk)
    except Exception:
        _mark(job, GenerationJob.Status.CHECK, "The saved response could not be imported. It is retained for inspection; no new paid request was made.")
