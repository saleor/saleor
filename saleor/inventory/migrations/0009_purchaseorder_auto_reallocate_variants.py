from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0008_nullable_poi_price_currency_country"),
    ]

    operations = [
        migrations.AddField(
            model_name="purchaseorder",
            name="auto_reallocate_variants",
            field=models.BooleanField(default=True),
        ),
    ]
