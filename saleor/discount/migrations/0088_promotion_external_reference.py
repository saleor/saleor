from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0087_merge_20250630_1332"),
    ]

    operations = [
        migrations.AddField(
            model_name="promotion",
            name="external_reference",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
