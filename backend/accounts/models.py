from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Invitation(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)

    def clean(self):
        super().clean()
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.user_id and previous.email != self.email:
                raise ValidationError({"email": "Deactivate this invitation and create another; linked accounts cannot change email here."})

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class LoginToken(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)


class StudentSession(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE)
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)


class RateBucket(models.Model):
    key = models.CharField(max_length=64, unique=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)
