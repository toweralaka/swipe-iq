from django.conf import settings
from django.core.exceptions import ValidationError


def require_configuration():
    if not settings.AI_GENERATION_ENABLED or not settings.OPENAI_API_KEY or not settings.AI_TEXT_MODEL:
        raise ValidationError("AI generation is off or missing its backend API key/model. Follow docs/ai-generation-setup.md.")
    if not 1 <= settings.AI_DAILY_JOB_LIMIT <= 100:
        raise ValidationError("Configure AI_DAILY_JOB_LIMIT between 1 and 100 (start with 5).")
    if not 5 <= settings.AI_REQUEST_TIMEOUT <= 120:
        raise ValidationError("Configure AI_REQUEST_TIMEOUT between 5 and 120 seconds.")
