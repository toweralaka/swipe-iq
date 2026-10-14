from django import forms
from .models import GenerationJob
from .services import INPUT_FIELDS


class GenerationForm(forms.ModelForm):
    request_token = forms.CharField(widget=forms.HiddenInput, max_length=1024)

    class Meta:
        model = GenerationJob
        fields = INPUT_FIELDS + ["request_token"]
        labels = {"brief": "What should the post be about?", "include_questions": "Generate three quiz questions"}
        help_texts = {"format": "AI-1 supports text. Images/memes and video arrive in later stages.",
                      "source_excerpt": "Paste checked teaching material, not candidate information. Links are not fetched automatically.",
                      "include_questions": "Leave unchecked for a post without a quiz. Human review is still required."}
        widgets = {"objective": forms.Textarea(attrs={"rows": 2}), "brief": forms.Textarea(attrs={"rows": 3}),
                   "syllabus_excerpt": forms.Textarea(attrs={"rows": 5}), "source_excerpt": forms.Textarea(attrs={"rows": 5}),
                   "source_reference": forms.Textarea(attrs={"rows": 2})}
