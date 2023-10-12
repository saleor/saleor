from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0053_drop_sales_indexes"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="sale",
                    name="categories",
                ),
                migrations.RemoveField(
                    model_name="sale",
                    name="collections",
                ),
                migrations.RemoveField(
                    model_name="sale",
                    name="products",
                ),
                migrations.RemoveField(
                    model_name="sale",
                    name="variants",
                ),
                migrations.AlterUniqueTogether(
                    name="salechannellisting",
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name="salechannellisting",
                    name="channel",
                ),
                migrations.RemoveField(
                    model_name="salechannellisting",
                    name="sale",
                ),
                migrations.AlterUniqueTogether(
                    name="saletranslation",
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name="saletranslation",
                    name="sale",
                ),
                migrations.RemoveField(
                    model_name="checkoutlinediscount",
                    name="sale",
                ),
                migrations.RemoveField(
                    model_name="orderdiscount",
                    name="sale",
                ),
                migrations.RemoveField(
                    model_name="orderlinediscount",
                    name="sale",
                ),
                migrations.DeleteModel(
                    name="Sale",
                ),
                migrations.DeleteModel(
                    name="SaleChannelListing",
                ),
                migrations.DeleteModel(
                    name="SaleTranslation",
                ),
            ],
        ),
    ]
