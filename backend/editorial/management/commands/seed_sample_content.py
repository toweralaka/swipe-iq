import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from editorial.models import Examination, Card, LearningUnit, LearningUnitVersion, Question, Subject, Topic
from editorial.syllabus import CELL_TOPIC, JAMB_BIOLOGY_URL


class Command(BaseCommand):
    help = "Seed five humorous Biology units as unreviewed drafts; preserve existing versions."

    @transaction.atomic
    def handle(self, *args, **options):
        samples = json.loads((Path(__file__).resolve().parents[2] / "data" / "biology_samples.json").read_text(encoding="utf-8"))
        examination, _ = Examination.objects.get_or_create(code="jamb", defaults={"name": "JAMB", "is_active": True})
        subject, _ = Subject.objects.get_or_create(examination=examination, name="Biology")
        topic, _ = Topic.objects.get_or_create(subject=subject, name=CELL_TOPIC)
        created_count = 0
        for sample in samples:
            unit, _ = LearningUnit.objects.get_or_create(key=sample["key"])
            version, created = LearningUnitVersion.objects.get_or_create(unit=unit, number=1, defaults={
                "title": sample["title"] + " — UNREVIEWED",
                "topic": topic, "objective": sample["objective"],
                "syllabus_reference": JAMB_BIOLOGY_URL,
                "ai_provenance": "Codex-assisted original sample draft, 2026-10-12. JAMB Section A, topic 1(b), supporting objectives ii–iv. Suggested fact-check source: OpenStax Biology 2e, 4.3 Eukaryotic Cells, https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells . Human review outstanding.",
            })
            if not created:
                self.stdout.write(f"Preserved {unit.key} v1.")
                continue
            for position, text in enumerate(sample["cards"], 1):
                Card.objects.create(version=version, position=position, text=text)
            for position, (prompt, choices, answer, explanation) in enumerate(sample["questions"], 1):
                Question.objects.create(version=version, position=position, prompt=prompt,
                    correct_choice=answer, explanation=explanation,
                    **{"choice_" + letter: text for letter, text in zip("abcd", choices)})
            created_count += 1
            self.stdout.write(f"Created draft: {sample['title']}")
        self.stdout.write(f"Created {created_count} units. No publication or review confirmations; existing content preserved.")
