from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0205_merge_20260615_1308"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariantchannellisting",
            name="is_available_for_purchase",
            field=models.BooleanField(db_default=True, default=True),
        ),
    ]
