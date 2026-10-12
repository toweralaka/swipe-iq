from django.contrib import admin
from .models import QuizAttempt


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "version", "number", "score", "total", "completed_at"]
    readonly_fields = [field.name for field in QuizAttempt._meta.fields]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
