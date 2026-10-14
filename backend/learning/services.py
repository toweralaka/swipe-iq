from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, ValidationError
from editorial.student_api import available_quiz_versions
from .models import QuizAttempt


class SubmissionConflict(APIException):
    status_code = 409
    default_detail = "This submission ID was already used with different answers. Retry the original submission."


@transaction.atomic
def submit_attempt(user, version_id, submission_id, answers):
    # Serialize submissions for one candidate; database constraints also protect retries.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    normalized = sorted(answers, key=lambda answer: answer["question_id"])
    existing = QuizAttempt.objects.filter(user=user, submission_id=submission_id).first()
    if existing:
        if existing.version_id != version_id or existing.answers != normalized:
            raise SubmissionConflict()
        return existing, False
    version = get_object_or_404(available_quiz_versions().select_for_update(), pk=version_id)
    questions = list(version.questions.all())
    expected = {question.pk for question in questions}
    if len(questions) != 3 or len(normalized) != 3 or {a["question_id"] for a in normalized} != expected:
        raise ValidationError({"answers": "Answer each of this quiz's three questions exactly once."})
    choices = {answer["question_id"]: answer["choice"] for answer in normalized}
    results = [{
        "question_id": question.pk, "position": question.position, "prompt": question.prompt,
        "choices": {c: getattr(question, "choice_" + c) for c in "abcd"},
        "selected_choice": choices[question.pk], "correct_choice": question.correct_choice,
        "is_correct": choices[question.pk] == question.correct_choice, "explanation": question.explanation,
    } for question in questions]
    subject = version.topic.subject
    latest = QuizAttempt.objects.filter(user=user, unit_id=version.unit_id).aggregate(number=Max("number"))["number"] or 0
    attempt = QuizAttempt.objects.create(user=user, unit_id=version.unit_id, version=version,
        submission_id=submission_id, number=latest + 1, answers=normalized, results=results,
        context={"title": version.title, "topic": version.topic.name, "subject": subject.name,
                 "examination": subject.examination.name, "unit_key": version.unit.key},
        score=sum(result["is_correct"] for result in results), total=3)
    return attempt, True
