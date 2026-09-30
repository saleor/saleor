from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0206_product_media_translation"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="external_reference",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
