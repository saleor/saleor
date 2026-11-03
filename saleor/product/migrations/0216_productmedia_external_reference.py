from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0215_productvariantchannellisting_is_available_for_purchase"),
    ]

    operations = [
        migrations.AddField(
            model_name="productmedia",
            name="external_reference",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
