# Generated by Django 3.0.6 on 2020-05-27 08:14

from django.db import migrations, models


def populate_product_variant_price(apps, schema_editor):
    ProductVariant = apps.get_model("product", "ProductVariant")
    for product_variant in ProductVariant.objects.iterator():
        price_override_amount = product_variant.price_override_amount
        if price_override_amount:
            product_variant.price_amount = price_override_amount
        else:
            product_price = product_variant.product.price_amount
            product_variant.price_amount = product_price

        product_variant.save(update_fields=["price_amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0117_auto_20200423_0737"),
    ]

    operations = [
        migrations.AddField(
            model_name="productvariant",
            name="price_amount",
            field=models.DecimalField(decimal_places=2, max_digits=12, null=True),
        ),
        migrations.RunPython(populate_product_variant_price),
        migrations.AlterField(
            model_name="productvariant",
            name="price_amount",
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.RemoveField(
            model_name="productvariant", name="price_override_amount",
        ),
        migrations.RemoveField(model_name="product", name="price_amount",),
        migrations.AlterField(
            model_name="product",
            name="minimal_variant_price_amount",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
    ]
