from django.db import migrations, models


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
        migrations.AddField(
            model_name="voucher",
            name="variants",
            field=models.ManyToManyField(blank=True, to="product.ProductVariant"),
        ),
    ]
