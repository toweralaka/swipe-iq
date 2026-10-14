import uuid
from django.db import IntegrityError, OperationalError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.exceptions import APIException


class RetrySubmission(APIException):
    status_code = 503
    default_detail = "Submission is busy. Retry the same submission ID and answers."
from accounts.views import StudentView
from editorial.student_api import available_quiz_versions, StudentPagination
from .models import QuizAttempt
from .services import submit_attempt


class AnswerInput(serializers.Serializer):
    question_id = serializers.IntegerField(min_value=1)
    choice = serializers.ChoiceField(choices=list("abcd"))


class AttemptInput(serializers.Serializer):
    version = serializers.IntegerField(min_value=1)
    submission_id = serializers.UUIDField()
    answers = AnswerInput(many=True, min_length=3, max_length=3)


class AttemptSummary(serializers.ModelSerializer):
    is_first = serializers.SerializerMethodField()
    def get_is_first(self, obj):
        return obj.number == 1
    class Meta:
        model = QuizAttempt
        fields = ["id", "version", "context", "number", "is_first", "score", "total", "completed_at"]


class AttemptDetail(AttemptSummary):
    class Meta(AttemptSummary.Meta):
        fields = AttemptSummary.Meta.fields + ["results"]


class QuizView(StudentView):
    def get(self, request, version_id):
        version = get_object_or_404(available_quiz_versions(), pk=version_id)
        questions = [{"id": q.pk, "position": q.position, "prompt": q.prompt,
                      "choices": {c: getattr(q, "choice_" + c) for c in "abcd"}} for q in version.questions.all()]
        return Response({"version": version.pk, "title": version.title, "submission_id": str(uuid.uuid4()), "questions": questions})


class AttemptList(StudentView, generics.ListAPIView):
    serializer_class = AttemptSummary
    pagination_class = StudentPagination
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)
    def post(self, request):
        data = AttemptInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            attempt, created = submit_attempt(request.user, data.validated_data["version"],
                data.validated_data["submission_id"], data.validated_data["answers"])
        except (IntegrityError, OperationalError):
            # The atomic service has rolled back; retries retain the same ID.
            raise RetrySubmission() from None
        return Response(AttemptDetail(attempt).data, status=201 if created else 200)


class AttemptResult(StudentView, generics.RetrieveAPIView):
    serializer_class = AttemptDetail
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)


class ProgressView(StudentView):
    def get(self, request):
        attempts = QuizAttempt.objects.filter(user=request.user)
        firsts = attempts.filter(number=1).aggregate(score=Sum("score"), total=Sum("total"))
        percentage = round(100 * firsts["score"] / firsts["total"], 1) if firsts["total"] else None
        return Response({"completed_units": attempts.values("unit_id").distinct().count(),
                         "total_attempts": attempts.count(), "first_attempt_percentage": percentage})
