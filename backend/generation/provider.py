import json
from django.conf import settings
from openai import OpenAI, APIConnectionError, APIStatusError
from .prompts import INSTRUCTIONS, PROMPT_VERSION, request_input
from .validation import output_schema


class GenerationFailure(Exception):
    def __init__(self, message, response_id="", usage=None):
        super().__init__(message)
        self.response_id = response_id
        self.usage = usage or {}


class UncertainGeneration(Exception):
    pass


def generate_text(job):
    if job.prompt_version != PROMPT_VERSION:
        raise GenerationFailure("This request uses an older prompt version. Open a new form; it was not sent to the provider.")
    # Disable SDK retries: an uncertain request must not silently incur another charge.
    try:
        with OpenAI(api_key=settings.OPENAI_API_KEY, base_url="https://api.openai.com/v1",
                    timeout=settings.AI_REQUEST_TIMEOUT, max_retries=0) as client:
            response = client.responses.create(model=job.model_name, instructions=INSTRUCTIONS,
                input=request_input(job), store=False, max_output_tokens=4000,
                text={"format": {"type": "json_schema", "name": "unreviewed_post", "strict": True, "schema": output_schema()}})
    except APIConnectionError:
        raise UncertainGeneration("The provider reply was not confirmed. Check the provider activity before submitting a new paid request.") from None
    except APIStatusError as error:
        if error.status_code >= 500:
            raise UncertainGeneration("The provider could not confirm the outcome. Check activity before requesting another generation.") from None
        raise GenerationFailure("Provider rejected the request. Check model access, funding, credentials, and rate limits before creating a new request.") from None
    usage = response.usage.model_dump(mode="json") if response.usage else {}
    if response.status != "completed":
        raise GenerationFailure("The response was incomplete or refused. No draft was imported.", response.id, usage)
    try:
        output = json.loads(response.output_text)
    except (ValueError, TypeError):
        raise GenerationFailure("The provider did not return readable draft data; it may have refused. No draft was imported.", response.id, usage) from None
    return {"output": output, "response_id": response.id, "usage": usage}
