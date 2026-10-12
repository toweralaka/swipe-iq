import django.db.models.deletion
from django.db import migrations, models


def assign_existing_subjects_to_jamb(apps, schema_editor):
    Examination = apps.get_model("editorial", "Examination")
    Subject = apps.get_model("editorial", "Subject")
    alias = schema_editor.connection.alias
    jamb, _ = Examination.objects.using(alias).get_or_create(
        code="jamb", defaults={"name": "JAMB", "is_active": True}
    )
    Subject.objects.using(alias).filter(examination__isnull=True).update(examination_id=jamb.pk)


class Migration(migrations.Migration):
    dependencies = [("editorial", "0001_initial")]
    operations = [
        migrations.CreateModel(name="Examination", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("code", models.SlugField(unique=True, help_text="Stable identifier, e.g. jamb or ssce.")),
            ("name", models.CharField(max_length=100, unique=True)),
            ("is_active", models.BooleanField(default=False, help_text="Only activate when content and student access are ready.")),
        ]),
        migrations.AddField(model_name="subject", name="examination", field=models.ForeignKey(
            null=True, related_name="subjects", on_delete=django.db.models.deletion.PROTECT, to="editorial.examination")),
        migrations.RunPython(assign_existing_subjects_to_jamb, migrations.RunPython.noop),
        migrations.AlterField(model_name="subject", name="name", field=models.CharField(max_length=100)),
        migrations.AlterField(model_name="subject", name="examination", field=models.ForeignKey(
            related_name="subjects", on_delete=django.db.models.deletion.PROTECT, to="editorial.examination")),
        migrations.AddConstraint(model_name="subject", constraint=models.UniqueConstraint(
            fields=["examination", "name"], name="unique_exam_subject")),
    ]
