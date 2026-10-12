from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ExaminationMigrationTests(TransactionTestCase):
    def test_existing_content_keeps_identity_and_publication_under_jamb(self):
        before = [("editorial", "0001_initial")]
        after = [("editorial", "0002_examination")]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            old = executor.loader.project_state(before).apps
            subject = old.get_model("editorial", "Subject").objects.create(name="Biology")
            topic = old.get_model("editorial", "Topic").objects.create(subject=subject, name="Cells")
            unit = old.get_model("editorial", "LearningUnit").objects.create(key="existing-cell-lesson")
            version = old.get_model("editorial", "LearningUnitVersion").objects.create(
                unit=unit, topic=topic, title="Existing approved lesson", objective="Compare cells", status="published")
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            new = executor.loader.project_state(after).apps
            migrated = new.get_model("editorial", "LearningUnitVersion").objects.get(pk=version.pk)
            self.assertEqual(migrated.topic_id, topic.pk)
            self.assertEqual(migrated.unit_id, unit.pk)
            self.assertEqual(migrated.title, "Existing approved lesson")
            self.assertEqual(migrated.status, "published")
            migrated_subject = new.get_model("editorial", "Subject").objects.get(pk=subject.pk)
            self.assertEqual(migrated_subject.examination.code, "jamb")
            self.assertTrue(migrated_subject.examination.is_active)
            self.assertEqual(new.get_model("editorial", "Examination").objects.count(), 1)
        finally:
            MigrationExecutor(connection).migrate(after)
