import logging
from django.http import HttpResponse, JsonResponse, Http404
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .authentication import StudentSessionAuthentication
from .services import exchange_token, rate_limit, request_link

logger = logging.getLogger(__name__)
GENERIC = "If this address is invited, a login link will arrive shortly."


class EmailInput(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class TokenInput(serializers.Serializer):
    token = serializers.RegexField(r"^[A-Za-z0-9_-]{43}$")


class PublicAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class RequestLinkView(PublicAuthView):
    def post(self, request):
        rate_limit("request-ip", request.META.get("REMOTE_ADDR", ""), 20)
        data = EmailInput(data=request.data)
        data.is_valid(raise_exception=True)
        email = data.validated_data["email"].strip().lower()
        rate_limit("request-email", email, 3)
        try:
            request_link(email)
        except Exception:
            # No exception text: providers can include recipients or message bodies.
            logger.error("Login email delivery failed; check email service configuration.")
        return Response({"detail": GENERIC}, status=202)


class ExchangeView(PublicAuthView):
    def post(self, request):
        rate_limit("exchange-ip", request.META.get("REMOTE_ADDR", ""), 30)
        data = TokenInput(data=request.data)
        data.is_valid(raise_exception=True)
        credential, session = exchange_token(data.validated_data["token"])
        return Response({"credential": credential, "expires_at": session.expires_at.isoformat()})


class StudentView(APIView):
    authentication_classes = [StudentSessionAuthentication]
    permission_classes = [IsAuthenticated]

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class MeView(StudentView):
    def get(self, request):
        return Response({"id": request.user.pk, "email": request.auth.invitation.email})


class LogoutView(StudentView):
    def post(self, request):
        request.auth.revoked_at = timezone.now()
        request.auth.save(update_fields=["revoked_at"])
        return Response(status=204)


def login_help(request):
    # Never consumes a token. Email scanners only see a static help page.
    response = HttpResponse("<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Swipe-IQ sign-in</title></head><body><h1>Sign in to Swipe-IQ</h1><p>Install the Android preview build supplied by your pilot organizer, then reopen your email link and confirm sign-in in the app.</p><p>If the app does not open, ask the organizer to check Android link settings. If the link has expired, request a new one in the app.</p></body></html>")
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    response["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


def assetlinks(request):
    fingerprints = settings.ANDROID_CERT_FINGERPRINTS
    if not fingerprints:
        raise Http404
    return JsonResponse([{"relation": ["delegate_permission/common.handle_all_urls"], "target": {
        "namespace": "android_app", "package_name": settings.ANDROID_PACKAGE,
        "sha256_cert_fingerprints": fingerprints}}], safe=False)
