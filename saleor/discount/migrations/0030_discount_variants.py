from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0150_collection_collection_search_gin"),
        ("discount", "0028_auto_20210817_1015"),
    ]

    operations = [
        migrations.AddField(
            model_name="sale",
            name="variants",
            field=models.ManyToManyField(blank=True, to="product.ProductVariant"),
        ),
        migrations.AddField(
            model_name="voucher",
            name="variants",
            field=models.ManyToManyField(blank=True, to="product.ProductVariant"),
        ),
    ]
