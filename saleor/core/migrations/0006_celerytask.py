from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_eventdelivery_webhook"),
    ]

    operations = [
        migrations.CreateModel(
            name="CeleryTask",
            fields=[
                (
                    "task_name",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
