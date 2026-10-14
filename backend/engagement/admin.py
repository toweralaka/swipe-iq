from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import path
from .models import Like, EngagementEvent
from .reporting import aggregate_report


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Like)
class LikeAdmin(ReadOnlyAdmin):
    list_display = ["unit", "card_identity", "is_active", "updated_at"]
    list_filter = ["is_active"]


@admin.register(EngagementEvent)
class EventAdmin(ReadOnlyAdmin):
    list_display = ["unit", "kind", "day", "received_at"]
    list_filter = ["kind", "day"]
    change_list_template = "admin/engagement/engagementevent/change_list.html"

    def get_urls(self):
        return [path("export/", self.admin_site.admin_view(self.export), name="engagement-export")] + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, {"can_export": request.user.has_perm("engagement.export_engagementevent"), **(extra_context or {})})

    def export(self, request):
        if not request.user.has_perm("engagement.export_engagementevent"):
            raise PermissionDenied
        try:
            report = aggregate_report(int(request.GET.get("days", "7")))
        except ValueError:
            return JsonResponse({"detail": "Choose days between 1 and 90."}, status=400)
        response = JsonResponse(report)
        response["Content-Disposition"] = 'attachment; filename="swipe-iq-engagement.json"'
        response["Cache-Control"] = "private, no-store"
        return response
