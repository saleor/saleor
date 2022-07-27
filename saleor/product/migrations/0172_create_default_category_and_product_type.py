from django.db import migrations

from ...product import ProductTypeKind


def create_default_category(apps, schema_editor):
    Category = apps.get_model("product", "Category")
    Category.objects.create(
        name="Default Category",
        slug="default-category",
        lft=0,
        rght=0,
        tree_id=0,
        level=0,
    )


def create_default_product_type(apps, schema_editor):
    ProductType = apps.get_model("product", "ProductType")
    ProductType.objects.create(
        name="Default Type",
        slug="default-type",
        kind=ProductTypeKind.NORMAL,
        has_variants=False,
        is_shipping_required=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0171_alter_versatile_images"),
        ("warehouse", "0031_create_default_warehouse"),
    ]

    operations = [
        migrations.RunPython(create_default_product_type),
        migrations.RunPython(create_default_category),
    ]
