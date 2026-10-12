from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .models import StudentSession
from .services import digest


class StudentSessionAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != b"bearer":
            raise AuthenticationFailed("Sign in again.")
        try:
            credential = parts[1].decode("ascii")
        except UnicodeDecodeError:
            raise AuthenticationFailed("Sign in again.")
        session = StudentSession.objects.select_related("invitation__user").filter(
            digest=digest(credential), revoked_at__isnull=True, expires_at__gt=timezone.now(),
            invitation__is_active=True, invitation__user__is_active=True,
            invitation__user__is_staff=False, invitation__user__is_superuser=False).first()
        if not session:
            raise AuthenticationFailed("Session expired or revoked. Request a new login link.")
        return session.invitation.user, session

    def authenticate_header(self, request):
        return "Bearer"
