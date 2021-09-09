from django.apps import apps
from django.db import migrations, models


def populate_variants_from_product_field(app, schema):
    SaleModel = apps.get_model("discount", "Sale")
    VariantsModel = apps.get_model("product", "ProductVariant")

    for sale in SaleModel.objects.iterator():
        product_qset = sale.products.prefetch_related("variants")
        variants_qset = VariantsModel.objects.filter(
            id__in=product_qset.values("variants")
        )
        variants_ids = [variant.id for variant in variants_qset]
        sale.variants.add(*variants_ids)


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0147_auto_20210817_1015"),
        ("discount", "0029_merge_0028_alter_voucher_code_0028_auto_20210817_1015"),
    ]

    operations = [
        migrations.AddField(
            model_name="sale",
            name="variants",
            field=models.ManyToManyField(blank=True, to="product.ProductVariant"),
        ),
        migrations.RunPython(populate_variants_from_product_field),
    ]
