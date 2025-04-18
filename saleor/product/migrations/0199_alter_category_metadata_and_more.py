# Generated by Django 5.2 on 2025-04-18 10:39

from django.db import migrations, models

import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0198_alter_collection_products"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="digitalcontent",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="digitalcontent",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="productmedia",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="productmedia",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="producttype",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="producttype",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="productvariant",
            name="metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
        migrations.AlterField(
            model_name="productvariant",
            name="private_metadata",
            field=models.JSONField(
                blank=True,
                db_default={},
                default=dict,
                encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
            ),
        ),
    ]
