from django import forms
from .models import GenerationJob
from .services import INPUT_FIELDS
from django.conf import settings
from .configuration import models_for_format


class GenerationForm(forms.ModelForm):
    model_name = forms.ChoiceField(label="AI model", help_text="Choose a configured text model. This request keeps your choice even if settings change later.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model_name"].choices = [(model, model) for model in models_for_format("text")]
        self.fields["model_name"].initial = settings.AI_TEXT_MODEL

    request_token = forms.CharField(widget=forms.HiddenInput, max_length=1024)

    class Meta:
        model = GenerationJob
        fields = INPUT_FIELDS + ["request_token"]
        labels = {"brief": "What should the post be about?", "include_questions": "Generate three quiz questions"}
        widgets = {"objective": forms.Textarea(attrs={"rows": 2}), "brief": forms.Textarea(attrs={"rows": 3}),
                   "syllabus_excerpt": forms.Textarea(attrs={"rows": 5}), "source_excerpt": forms.Textarea(attrs={"rows": 5}),
                   "source_reference": forms.Textarea(attrs={"rows": 2})}
