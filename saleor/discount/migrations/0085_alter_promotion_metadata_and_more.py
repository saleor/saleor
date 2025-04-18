# Generated by Django 5.2 on 2025-04-18 10:39

from django.db import migrations, models

import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0084_set_missing_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="promotion",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="promotion",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="voucher",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="voucher",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
    ]
