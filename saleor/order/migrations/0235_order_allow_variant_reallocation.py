from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("order", "0234_alter_order_inco_term")]
    operations = [
        migrations.AddField(
            model_name="order",
            name="allow_variant_reallocation",
            field=models.BooleanField(default=True),
        ),
    ]
