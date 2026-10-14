from django.db import IntegrityError, OperationalError
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from accounts.views import StudentView
from .models import Like, EngagementEvent
from .services import available_card, set_like, record_event


class Busy(APIException):
    status_code = 503
    default_detail = "Could not confirm this change. Check its current state before retrying."


class LikeInput(serializers.Serializer):
    liked = serializers.BooleanField()


class LikeView(StudentView):
    def get(self, request, version_id, identity):
        card = available_card(version_id, identity)
        liked = Like.objects.filter(user=request.user, unit_id=card.version.unit_id,
                                    card_identity=identity, is_active=True).exists()
        return Response({"liked": liked})

    def post(self, request, version_id, identity):
        data = LikeInput(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            liked = set_like(request.user, version_id, identity, data.validated_data["liked"])
        except (IntegrityError, OperationalError):
            raise Busy() from None
        return Response({"liked": liked})


class EventInput(serializers.Serializer):
    version = serializers.IntegerField(min_value=1)
    card_identity = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=EngagementEvent.Kind.values)


class EventView(StudentView):
    def post(self, request):
        data = EventInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        try:
            row, created = record_event(request.user, values["version"], values["card_identity"], values["kind"])
        except (IntegrityError, OperationalError):
            raise Busy() from None
        return Response({"recorded": True, "day": row.day.isoformat()}, status=201 if created else 200)
