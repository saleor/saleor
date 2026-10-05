from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0210_collection_external_reference_unique_constraint"),
    ]

    operations = [
        migrations.AddField(
            model_name="productmedia",
            name="external_reference",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
