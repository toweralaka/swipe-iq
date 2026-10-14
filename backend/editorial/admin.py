from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.html import format_html
from .models import Examination, Card, LearningUnit, LearningUnitVersion, MediaAsset, Question, Subject, Topic
from .services import publish, replacement_draft, withdraw


class NoBulkDeleteAdmin(admin.ModelAdmin):
    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


class FrozenInline(admin.StackedInline):
    extra = 0

    def has_add_permission(self, request, obj=None):
        return (obj is None or obj.status == "draft") and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return (obj is None or obj.status == "draft") and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return (obj is None or obj.status == "draft") and super().has_delete_permission(request, obj)


class CardInline(FrozenInline):
    model = Card
    max_num = 1
    verbose_name_plural = "Content card — one per post; keep existing history"


class QuestionInline(FrozenInline):
    model = Question
    max_num = 3
    verbose_name_plural = "Optional quiz — leave empty or add exactly three questions"


@admin.register(LearningUnitVersion)
class VersionAdmin(NoBulkDeleteAdmin):
    list_display = ["title", "examination", "number", "status", "reviewer", "published_at"]
    list_filter = ["status", "topic__subject__examination", "topic"]
    search_fields = ["title", "objective"]
    inlines = [CardInline, QuestionInline]
    readonly_fields = ["status", "reviewer", "reviewed_at", "published_at", "withdrawn_at"]
    actions = ["publish_selected", "withdraw_selected", "copy_to_draft"]

    @admin.display(description="Examination", ordering="topic__subject__examination__name")
    def examination(self, obj):
        return obj.topic.subject.examination.name

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != "draft":
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return (obj is None or obj.status == "draft") and super().has_change_permission(request, obj)

    def has_publish_permission(self, request):
        return request.user.has_perm("editorial.publish_learningunitversion")

    def transition(self, request, queryset, action):
        for version in queryset:
            try:
                action(version.pk, request.user)
            except (ValidationError, PermissionDenied) as error:
                detail = "; ".join(error.messages) if isinstance(error, ValidationError) else str(error)
                self.message_user(request, f"{version}: {detail}", messages.ERROR)
            else:
                self.message_user(request, f"Updated {version.title}.", messages.SUCCESS)

    @admin.action(description="Publish selected reviewed drafts", permissions=["publish"])
    def publish_selected(self, request, queryset):
        self.transition(request, queryset, publish)

    @admin.action(description="Withdraw selected published versions", permissions=["publish"])
    def withdraw_selected(self, request, queryset):
        self.transition(request, queryset, withdraw)

    @admin.action(description="Create replacement drafts (review resets)", permissions=["add"])
    def copy_to_draft(self, request, queryset):
        for version in queryset:
            draft = replacement_draft(version.pk)
            self.message_user(request, f"Created {draft}.", messages.SUCCESS)


@admin.register(MediaAsset)
class MediaAdmin(NoBulkDeleteAdmin):
    list_display = ["id", "kind", "byte_size", "metadata_checked"]
    list_filter = ["kind", "metadata_checked"]
    readonly_fields = ["byte_size", "preview"]

    @admin.display(description="Staff-only preview")
    def preview(self, obj):
        if obj and obj.file:
            return format_html('<a href="{}" target="_blank" rel="noopener">Open media</a>', obj.file.url)
        return "Save the asset first."

    def frozen(self, obj):
        return obj and obj.cards.exclude(version__status="draft").exists()

    def get_readonly_fields(self, request, obj=None):
        if self.frozen(obj):
            return [f.name for f in self.model._meta.fields] + ["preview"]
        return self.readonly_fields

    def has_change_permission(self, request, obj=None):
        return not self.frozen(obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Retain files for history; orphan cleanup is a later maintenance task.
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LearningUnit)
class UnitAdmin(NoBulkDeleteAdmin):
    list_display = ["key", "author"]

    def save_model(self, request, obj, form, change):
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Examination)
class ExaminationAdmin(NoBulkDeleteAdmin):
    list_display = ["name", "code", "is_active"]
    list_filter = ["is_active"]


@admin.register(Subject)
class SubjectAdmin(NoBulkDeleteAdmin):
    list_display = ["name", "examination"]
    list_filter = ["examination"]


@admin.register(Topic)
class TopicAdmin(NoBulkDeleteAdmin):
    list_display = ["name", "subject"]
    list_filter = ["subject__examination", "subject"]
