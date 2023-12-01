from django.db import migrations, models

import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0063_basediscount_voucher_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="promotionrule",
            name="catalogue_predicate",
            field=models.JSONField(
                blank=True,
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
    ]
