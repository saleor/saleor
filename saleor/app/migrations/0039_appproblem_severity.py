from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0038_add_app_problem"),
    ]

    operations = [
        migrations.AddField(
            model_name="appproblem",
            name="severity",
            field=models.CharField(
                choices=[("warning", "Warning"), ("error", "Error")],
                default="error",
                max_length=32,
            ),
        ),
    ]
