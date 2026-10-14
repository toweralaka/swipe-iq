import uuid
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from django.utils import timezone
from django.db.models import CharField, Value
from django.db.models.functions import MD5, Cast, Concat
import mimetypes
from django.db.models import OuterRef, Subquery, Q, Count, Exists
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from accounts.views import StudentView
from .models import Card, Examination, LearningUnitVersion, MediaAsset, Subject, Topic, Question


def available_versions():
    latest = LearningUnitVersion.objects.filter(unit_id=OuterRef("unit_id"), status="published").order_by("-number").values("pk")[:1]
    complete_quiz = Question.objects.filter(version_id=OuterRef("pk")).values("version_id").annotate(total=Count("pk")).filter(total=3)
    return LearningUnitVersion.objects.annotate(quiz_available=Exists(complete_quiz)).filter(
        status="published", topic__subject__examination__is_active=True,
        pk=Subquery(latest)).select_related("topic__subject__examination").order_by("pk")


def available_quiz_versions():
    return available_versions().filter(quiz_available=True)


class ExaminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Examination
        fields = ["id", "code", "name"]


class SubjectSerializer(serializers.ModelSerializer):
    examination = ExaminationSerializer(read_only=True)
    class Meta:
        model = Subject
        fields = ["id", "name", "examination"]


class TopicSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    class Meta:
        model = Topic
        fields = ["id", "name", "subject"]


class MediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    def get_url(self, obj):
        return f"/api/v1/media/{obj.pk}/"
    class Meta:
        model = MediaAsset
        fields = ["id", "kind", "byte_size", "duration_seconds", "alt_text", "transcript", "captions_vtt", "attribution", "url"]


class CardSerializer(serializers.ModelSerializer):
    media = MediaSerializer(read_only=True)
    class Meta:
        model = Card
        fields = ["identity", "position", "text", "media"]


class UnitSerializer(serializers.ModelSerializer):
    topic = TopicSerializer(read_only=True)
    unit_key = serializers.CharField(source="unit.key", read_only=True)
    quiz_available = serializers.BooleanField(read_only=True)
    class Meta:
        model = LearningUnitVersion
        fields = ["id", "unit_key", "number", "title", "objective", "topic", "quiz_available"]


class UnitDetailSerializer(UnitSerializer):
    cards = CardSerializer(many=True, read_only=True)
    class Meta(UnitSerializer.Meta):
        fields = UnitSerializer.Meta.fields + ["cards"]


class StudentPagination(PageNumberPagination):
    page_size = 20


class StudentList(StudentView, generics.ListAPIView):
    pagination_class = StudentPagination


class ExaminationList(StudentList):
    serializer_class = ExaminationSerializer
    def get_queryset(self):
        return Examination.objects.filter(is_active=True, subjects__topic__learningunitversion__in=available_versions()).distinct().order_by("name", "pk")


class SubjectList(StudentList):
    serializer_class = SubjectSerializer
    def get_queryset(self):
        query = Subject.objects.filter(topic__learningunitversion__in=available_versions()).select_related("examination").distinct().order_by("name", "pk")
        code = self.request.query_params.get("examination")
        return query.filter(examination__code=code) if code else query


class TopicList(StudentList):
    serializer_class = TopicSerializer
    def get_queryset(self):
        query = Topic.objects.filter(learningunitversion__in=available_versions()).select_related("subject__examination").distinct().order_by("name", "pk")
        subject = self.request.query_params.get("subject")
        if subject and not subject.isdigit():
            return query.none()
        return query.filter(subject_id=subject) if subject else query


class UnitList(StudentList):
    serializer_class = UnitSerializer
    def get_queryset(self):
        query = available_versions().select_related("unit")
        topic = self.request.query_params.get("topic")
        if topic and not topic.isdigit():
            return query.none()
        return query.filter(topic_id=topic) if topic else query


class UnitDetail(StudentView, generics.RetrieveAPIView):
    serializer_class = UnitDetailSerializer
    def get_queryset(self):
        return available_versions().select_related("unit").prefetch_related("cards__media")


class StudentMedia(StudentView):
    def get(self, request, asset_id):
        asset = get_object_or_404(MediaAsset.objects.filter(cards__version__in=available_versions()).distinct(), pk=asset_id)
        try:
            file = asset.file.open("rb")
        except OSError:
            raise Http404
        response = FileResponse(file, content_type=mimetypes.guess_type(asset.file.name)[0] or "application/octet-stream")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class AvailabilityInput(serializers.Serializer):
    version_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=200)


class UnitAvailability(StudentView):
    def post(self, request):
        data = AvailabilityInput(data=request.data)
        data.is_valid(raise_exception=True)
        ids = available_versions().filter(pk__in=data.validated_data["version_ids"]).values_list("pk", flat=True)
        return Response({"available_ids": list(ids)})


class FeedInput(serializers.Serializer):
    mix = serializers.RegexField(r"^[0-9a-f]{32}$", required=False)
    before = serializers.DateTimeField(required=False)
    subjects = serializers.CharField(max_length=220)
    q = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")

    def validate_q(self, value):
        if len(value.split()) > 10:
            raise serializers.ValidationError("Use 10 words or fewer in your search.")
        return value

    def validate_subjects(self, value):
        parts = value.split(",")
        if len(parts) > 20 or not all(part.isascii() and part.isdigit() and 0 < int(part) <= 2147483647 for part in parts):
            raise serializers.ValidationError("Choose between 1 and 20 subjects.")
        return sorted(set(int(part) for part in parts))


class FeedPagination(CursorPagination):
    page_size = 10
    ordering = ("shuffle_key", "pk")

    def paginate_queryset(self, queryset, request, view=None):
        self.mix = view.mix
        self.before = view.before.isoformat()
        self.count = queryset.count()
        return super().paginate_queryset(queryset, request, view)

    def mix_link(self, url):
        if not url:
            return None
        parts = urlsplit(url)
        params = dict(parse_qsl(parts.query))
        params.update(mix=self.mix, before=self.before)
        return urlunsplit(parts._replace(query=urlencode(params)))

    def get_paginated_response(self, data):
        return Response({"count": self.count, "next": self.mix_link(self.get_next_link()),
                         "mix": self.mix, "results": data})


class FeedList(StudentList):
    serializer_class = UnitDetailSerializer
    pagination_class = FeedPagination

    def get_queryset(self):
        inputs = FeedInput(data=self.request.query_params)
        inputs.is_valid(raise_exception=True)
        data = inputs.validated_data
        self.mix = data.get("mix", uuid.uuid4().hex)
        self.before = min(data.get("before", timezone.now()), timezone.now())
        query = available_versions().filter(topic__subject_id__in=data["subjects"], published_at__lte=self.before)
        for term in data["q"].split():
            query = query.filter(Q(title__icontains=term) | Q(objective__icontains=term)
                | Q(cards__text__icontains=term) | Q(topic__name__icontains=term)
                | Q(topic__subject__name__icontains=term))
        return query.annotate(shuffle_key=MD5(Concat(Value(self.mix), Cast("pk", CharField())))).select_related("unit").prefetch_related("cards__media").distinct().order_by("shuffle_key", "pk")
