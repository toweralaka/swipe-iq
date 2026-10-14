import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from editorial.models import Examination, Subject, Topic, LearningUnit, LearningUnitVersion, Card


class Command(BaseCommand):
    help = "Add five Government and five Chemistry one-card JAMB drafts. Preserve existing posts."

    @transaction.atomic
    def handle(self, *args, **options):
        samples = json.loads((Path(__file__).resolve().parents[2] / "data" / "jamb_subject_samples.json").read_text(encoding="utf-8"))
        examination, _ = Examination.objects.get_or_create(code="jamb", defaults={"name": "JAMB", "is_active": True})
        created = 0
        for sample in samples:
            if LearningUnit.objects.filter(key=sample["key"]).exists():
                self.stdout.write(f"Preserved {sample['key']}.")
                continue
            subject, _ = Subject.objects.get_or_create(examination=examination, name=sample["subject"])
            topic, _ = Topic.objects.get_or_create(subject=subject, name=sample["topic"])
            unit = LearningUnit.objects.create(key=sample["key"])
            version = LearningUnitVersion.objects.create(
                unit=unit, number=1, title=sample["title"] + " — UNREVIEWED",
                topic=topic, objective=sample["objective"], syllabus_reference=sample["syllabus_reference"],
                ai_provenance="Codex-assisted original sample, 2026-10-14. Topic mapping based on official JAMB IBASS syllabus search results; direct PDF retrieval returned the site shell. Human must verify syllabus mapping, teaching references, accuracy, humour, and analogy limits.")
            Card.objects.create(version=version, position=1, text=sample["text"])
            created += 1
            self.stdout.write(f"Created {sample['key']}.")
        self.stdout.write(f"Created {created} draft posts. No questions, media, review confirmations, or publication. Existing posts preserved.")
