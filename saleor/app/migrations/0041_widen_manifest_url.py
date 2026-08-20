from django.db import migrations, models


class Migration(migrations.Migration):
    """Widen ``manifest_url`` from varchar(200) to varchar(2048).

    Increasing a varchar length limit is a catalog-only change in PostgreSQL
    (>= 9.2) — no table rewrite, the ACCESS EXCLUSIVE lock is held momentarily.
    """

    dependencies = [
        ("app", "0040_appextension_identifier_unique_constraint"),
    ]

    operations = [
        migrations.AlterField(
            model_name="app",
            name="manifest_url",
            field=models.URLField(blank=True, max_length=2048, null=True),
        ),
        migrations.AlterField(
            model_name="appinstallation",
            name="manifest_url",
            field=models.URLField(max_length=2048),
        ),
    ]
