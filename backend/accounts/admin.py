from django.contrib import admin
from .models import Invitation, StudentSession


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["email"]
    fields = ["email", "is_active"]


@admin.register(StudentSession)
class StudentSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "invitation", "expires_at", "revoked_at"]
    readonly_fields = ["invitation", "expires_at", "revoked_at"]
    exclude = ["digest"]
    actions = ["revoke"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Revoke selected student sessions", permissions=["change"])
    def revoke(self, request, queryset):
        from django.utils import timezone
        queryset.update(revoked_at=timezone.now())
