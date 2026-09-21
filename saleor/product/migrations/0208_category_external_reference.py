from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0207_remove_producttype_is_digital_from_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="external_reference",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
