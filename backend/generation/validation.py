from rest_framework import serializers


class Choices(serializers.Serializer):
    a = serializers.CharField(max_length=300)
    b = serializers.CharField(max_length=300)
    c = serializers.CharField(max_length=300)
    d = serializers.CharField(max_length=300)

    def validate(self, values):
        if len({value.strip().casefold() for value in values.values()}) != 4:
            raise serializers.ValidationError("Choices must be distinct.")
        return values


class GeneratedQuestion(serializers.Serializer):
    prompt = serializers.CharField(max_length=600)
    choices = Choices()
    correct_choice = serializers.ChoiceField(choices=list("abcd"))
    explanation = serializers.CharField(max_length=800)


class GeneratedDraft(serializers.Serializer):
    title = serializers.CharField(max_length=160)
    card_text = serializers.CharField(max_length=900)
    questions = GeneratedQuestion(many=True, max_length=3)
    verification_notes = serializers.CharField(max_length=2000)


def validate_output(output, include_questions):
    data = GeneratedDraft(data=output)
    data.is_valid(raise_exception=True)
    if len(data.validated_data["questions"]) != (3 if include_questions else 0):
        raise serializers.ValidationError("Question count does not match the request.")
    return data.validated_data


def output_schema():
    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    text = {"type": "string"}
    question = obj({"prompt": text, "choices": obj({letter: text for letter in "abcd"}),
                    "correct_choice": {"type": "string", "enum": list("abcd")}, "explanation": text})
    return obj({"title": text, "card_text": text, "questions": {"type": "array", "items": question}, "verification_notes": text})
