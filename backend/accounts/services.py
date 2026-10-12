import hashlib
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import AuthenticationFailed, Throttled
from .models import Invitation, LoginToken, RateBucket, StudentSession


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def rate_limit(scope, value, limit, seconds=900):
    now = timezone.now()
    window = int(now.timestamp()) // seconds
    key = salted_hmac("student-rate", f"{scope}:{value}:{window}").hexdigest()
    bucket, _ = RateBucket.objects.get_or_create(key=key, defaults={"expires_at": now + timedelta(seconds=seconds)})
    # Conditional SQL increment prevents simultaneous requests from bypassing the limit.
    if not RateBucket.objects.filter(pk=bucket.pk, count__lt=limit).update(count=models.F("count") + 1):
        raise Throttled(wait=seconds - int(now.timestamp()) % seconds)


def request_link(email):
    invitation = Invitation.objects.select_related("user").filter(email=email, is_active=True).first()
    if not invitation or (invitation.user and (not invitation.user.is_active or invitation.user.is_staff or invitation.user.is_superuser)):
        return
    base = settings.LOGIN_LINK_BASE_URL
    parsed = urlsplit(base)
    if not parsed.netloc or parsed.path != "/login" or parsed.query or parsed.fragment or (parsed.scheme != "https" and not (settings.DEBUG and parsed.scheme == "http")):
        raise ValueError("LOGIN_LINK_BASE_URL must be an HTTPS /login URL (HTTP only in DEBUG).")
    raw = secrets.token_urlsafe(32)
    token = LoginToken.objects.create(invitation=invitation, digest=digest(raw), expires_at=timezone.now() + timedelta(minutes=15))
    try:
        # Fragment keeps the secret out of web-server request URLs and access logs.
        send_mail("Your Swipe-IQ login link", f"Open this link on your Android phone and confirm sign-in. It expires in 15 minutes and works once.\n\n{base}#token={raw}\n\nIf you did not request this, ignore it.", settings.DEFAULT_FROM_EMAIL, [email])
    except Exception:
        token.delete()
        # The view returns the same generic response; no address or token is logged.
        raise


@transaction.atomic
def exchange_token(raw):
    now = timezone.now()
    token = LoginToken.objects.filter(digest=digest(raw)).first()
    if not token:
        raise AuthenticationFailed("Link expired, already used, or invalid. Request a new link.")
    invitation = Invitation.objects.select_for_update().select_related("user").get(pk=token.invitation_id)
    if not invitation.is_active:
        raise AuthenticationFailed("Link expired, already used, or invalid. Request a new link.")
    if invitation.user and (not invitation.user.is_active or invitation.user.is_staff or invitation.user.is_superuser):
        raise AuthenticationFailed("Link expired, already used, or invalid. Request a new link.")
    # A conditional update consumes the token once, even across concurrent exchanges.
    if not LoginToken.objects.filter(pk=token.pk, consumed_at__isnull=True, expires_at__gt=now).update(consumed_at=now):
        raise AuthenticationFailed("Link expired, already used, or invalid. Request a new link.")
    if not invitation.user:
        user = get_user_model()(username="candidate-" + uuid.uuid4().hex, email=invitation.email)
        user.set_unusable_password()
        user.save()
        invitation.user = user
        invitation.save()
    credential = secrets.token_urlsafe(32)
    session = StudentSession.objects.create(invitation=invitation, digest=digest(credential), expires_at=now + timedelta(days=30))
    return credential, session
