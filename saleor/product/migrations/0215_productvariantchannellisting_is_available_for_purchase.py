from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0214_collection_translation_full_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariantchannellisting",
            name="is_available_for_purchase",
            field=models.BooleanField(db_default=True, default=True),
        ),
    ]
