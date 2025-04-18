# Generated by Django 5.2 on 2025-04-18 10:39

from django.db import migrations, models

import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("plugins", "0010_auto_20220104_1239"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pluginconfiguration",
            name="configuration",
            field=models.JSONField(
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
    ]
