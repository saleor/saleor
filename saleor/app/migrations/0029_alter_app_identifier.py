from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0028_set_identifier"),
    ]

    operations = [
        migrations.AlterField(
            model_name="app",
            name="identifier",
            field=models.CharField(max_length=256, blank=True),
        ),
    ]
