import uuid
from django.contrib import admin
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from .forms import GenerationForm
from .models import GenerationJob
from .services import enqueue, require_generator

TOKEN_SALT = "generation-request-v1"


@admin.register(GenerationJob)
class GenerationAdmin(admin.ModelAdmin):
    list_display = ["id", "topic", "format", "include_questions", "status", "created_at"]
    list_filter = ["status", "format", "include_questions"]
    actions = None
    readonly_fields = [field.name for field in GenerationJob._meta.fields] + ["draft_link"]

    def has_add_permission(self, request):
        return request.user.has_perm("generation.generate_content")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Open draft for human review")
    def draft_link(self, obj):
        if obj.result_version_id:
            return format_html('<a href="{}">Review the unreviewed draft</a>', reverse("admin:editorial_learningunitversion_change", args=[obj.result_version_id]))
        return "No draft yet. Refresh this page to check saved progress."

    def add_view(self, request, form_url="", extra_context=None):
        require_generator(request.user)
        token = signing.dumps({"id": str(uuid.uuid4()), "user": request.user.pk}, salt=TOKEN_SALT)
        form = GenerationForm(request.POST if request.method == "POST" else None, initial={"request_token": token})
        if request.method == "POST" and form.is_valid():
            try:
                data = signing.loads(form.cleaned_data["request_token"], salt=TOKEN_SALT, max_age=86400)
                if data["user"] != request.user.pk:
                    raise PermissionDenied
                request_id = uuid.UUID(data["id"])
                values = {field: form.cleaned_data[field] for field in GenerationForm.Meta.fields if field != "request_token"}
                job = enqueue(request.user, request_id, values)
            except (signing.BadSignature, KeyError, ValueError):
                form.add_error(None, "This generation form expired or is invalid. Open a new form.")
            except ValidationError as error:
                form.add_error(None, "; ".join(error.messages))
            except (IntegrityError, OperationalError):
                form.add_error(None, "The database is busy. Submit this same form again to check/create its request safely.")
            else:
                return HttpResponseRedirect(reverse("admin:generation_generationjob_change", args=[job.pk]))
        context = {**self.admin_site.each_context(request), "title": "Generate a new unreviewed text post",
                   "opts": self.model._meta, "form": form, **(extra_context or {})}
        return TemplateResponse(request, "admin/generation/request.html", context)
