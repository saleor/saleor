from django.db import migrations


def move_tax_rate_to_meta(apps, schema_editor):
    ProductType = apps.get_model("product", "ProductType")
    Product = apps.get_model("product", "Product")
    product_types = ProductType.objects.filter(tax_rate__isnull=False).exclude(
        tax_rate=""
    )
    products = Product.objects.filter(tax_rate__isnull=False).exclude(tax_rate="")
    product_types_list = []
    for product_type in product_types:
        if "taxes" not in product_type.meta:
            product_type.meta["taxes"] = {}
        product_type.meta["taxes"]["vatlayer"] = {
            "code": product_type.tax_rate,
            "description": product_type.tax_rate,
        }
        product_types_list.append(product_type)
    ProductType.objects.bulk_update(product_types_list, ["meta"])

    product_list = []
    for product in products:
        if "taxes" not in product.meta:
            product.meta["taxes"] = {}
        product.meta["taxes"]["vatlayer"] = {
            "code": product.tax_rate,
            "description": product.tax_rate,
        }
        product_list.append(product)
    Product.objects.bulk_update(product_list, ["meta"])


class Migration(migrations.Migration):
    dependencies = [("product", "0094_auto_20190618_0430")]

    operations = [
        migrations.RunPython(move_tax_rate_to_meta),
        migrations.RemoveField(model_name="product", name="tax_rate"),
        migrations.RemoveField(model_name="producttype", name="tax_rate"),
    ]
