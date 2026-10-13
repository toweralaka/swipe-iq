from django.core.management.base import BaseCommand
from django.db import transaction
from editorial.models import Examination, Card, LearningUnit, LearningUnitVersion, Question, Subject, Topic
from editorial.services import CHECKS
from editorial.syllabus import CELL_OBJECTIVE, CELL_TOPIC, JAMB_BIOLOGY_URL, LEGACY_OBJECTIVE, LEGACY_TOPIC


class Command(BaseCommand):
    help = "Create unreviewed demo drafts; never overwrite existing content or publish."

    def add_arguments(self, parser):
        parser.add_argument("--align-syllabus", action="store_true", help="Align only untouched legacy demo mapping; preserve edited/reviewed/published drafts.")

    @transaction.atomic
    def handle(self, *args, **options):
        examination, _ = Examination.objects.get_or_create(code="jamb", defaults={"name": "JAMB", "is_active": True})
        subject, _ = Subject.objects.get_or_create(examination=examination, name="Biology")
        topic, _ = Topic.objects.get_or_create(subject=subject, name=CELL_TOPIC)
        data = [
            ("demo-cell-comparison", "Plant and animal cells — UNREVIEWED DEMO", [
                "A plant cell brings a wall to the party; an animal cell travels without one. Both still have a cell membrane. Analogy only: check the scientific explanation before publication.",
                "Chloroplasts occur in photosynthetic plant cells; not every plant cell contains them. Both plant and animal cells have mitochondria.",
            ]),
            ("demo-cell-media", "Cell revision media — UNREVIEWED DEMO", [
                "IMAGE SLOT: attach a labelled plant/animal cell diagram you own or may use. Text must explain the comparison without the image.",
                "AUDIO SLOT: attach a short checked narration about cell structures and their functions, with its transcript.",
                "VIDEO SLOT: attach a short captioned explanation; clarify that a cell wall and membrane have different roles.",
            ]),
        ]
        for key, title, texts in data:
            unit, _ = LearningUnit.objects.get_or_create(key=key)
            version, created = LearningUnitVersion.objects.get_or_create(unit=unit, number=1, defaults={
                "title": title, "topic": topic,
                "objective": CELL_OBJECTIVE,
                "syllabus_reference": JAMB_BIOLOGY_URL,
                "ai_provenance": "Agent-assisted seed draft; not a human-reviewed lesson.",
            })
            if not created:
                untouched_mapping = (
                    version.status == "draft" and version.objective == LEGACY_OBJECTIVE
                    and version.topic.name == LEGACY_TOPIC
                    and version.syllabus_reference == JAMB_BIOLOGY_URL
                    and not any(getattr(version, check) for check in CHECKS)
                    and not version.reviewer_id and not version.review_notes.strip()
                    and not version.source_reference.strip()
                )
                if options["align_syllabus"] and untouched_mapping:
                    version.topic = topic
                    version.objective = CELL_OBJECTIVE
                    version.save()
                    self.stdout.write(f"Aligned legacy mapping for {unit.key}; content remains unreviewed.")
                self.stdout.write(f"Preserved existing {unit.key} v1 content.")
                continue
            Card.objects.create(version=version, position=1, text="\n\n".join(texts))
            questions = [
                ("Which structure occurs in both typical plant and animal cells?", ["Cell membrane", "Cell wall", "Chloroplast", "Large permanent central vacuole"], "a", "Both have a cell membrane that regulates movement into and out of the cell."),
                ("Which statement about chloroplasts is most accurate?", ["Every plant cell contains them", "Photosynthetic plant cells contain them", "Animal cells use them for respiration", "They replace the nucleus"], "b", "Chloroplasts carry out photosynthesis; non-photosynthetic plant cells may lack them."),
                ("Which structure helps provide rigid support in plant cells?", ["Cell membrane only", "Mitochondrion", "Cell wall", "Nucleus"], "c", "The cell wall contributes structural support outside the cell membrane."),
            ]
            for position, (prompt, choices, correct, explanation) in enumerate(questions, 1):
                Question.objects.create(version=version, position=position, prompt=prompt,
                    correct_choice=correct, explanation=explanation,
                    **{"choice_" + letter: value for letter, value in zip("abcd", choices)})
            self.stdout.write(f"Created {unit.key}: unreviewed draft, no media uploaded.")
        self.stdout.write("No publication performed. Attach real reviewed media; complete checklist/reference notes in admin.")
