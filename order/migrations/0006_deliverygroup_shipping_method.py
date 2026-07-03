from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("order", "0005_deliverygroup_last_updated")]

    operations = [
        migrations.AddField(
            model_name="deliverygroup",
            name="shipping_method",
            field=models.CharField(default="", max_length=255, db_index=True),
        )
    ]
