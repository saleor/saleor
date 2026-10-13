from django.db import migrations, models


class Migration(migrations.Migration):
    """Remove the preorder allocation and reservation models from the Django state.

    The whole GraphQL surface of the preorder feature was removed in Saleor
    3.24.0, but the tables have to stay for one release so that pods running
    the previous version keep working during a rolling deploy.
    """

    dependencies = [
        ("warehouse", "0035_alter_warehouse_metadata_and_more"),
        ("product", "0208_remove_preorder_fields_from_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # 'db_constraint=False' drops the FKs from the DB, which prevents
                # errors when deleting in cascade due to Django no longer knowing
                # about the existence of the preorder tables.
                migrations.AlterField(
                    model_name="preorderallocation",
                    name="order_line",
                    field=models.ForeignKey(
                        "order.OrderLine",
                        related_name="preorder_allocations",
                        on_delete=models.CASCADE,
                        db_constraint=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="preorderallocation",
                    name="product_variant_channel_listing",
                    field=models.ForeignKey(
                        "product.ProductVariantChannelListing",
                        related_name="preorder_allocations",
                        on_delete=models.CASCADE,
                        db_constraint=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="preorderreservation",
                    name="checkout_line",
                    field=models.ForeignKey(
                        "checkout.CheckoutLine",
                        related_name="preorder_reservations",
                        on_delete=models.CASCADE,
                        db_constraint=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="preorderreservation",
                    name="product_variant_channel_listing",
                    field=models.ForeignKey(
                        "product.ProductVariantChannelListing",
                        related_name="preorder_reservations",
                        on_delete=models.CASCADE,
                        db_constraint=False,
                    ),
                ),
            ],
            # Will be dropped from the actual DB in Saleor v3.25.0
            state_operations=[
                migrations.RemoveField(
                    model_name="preorderallocation",
                    name="order_line",
                ),
                migrations.RemoveField(
                    model_name="preorderallocation",
                    name="product_variant_channel_listing",
                ),
                migrations.RemoveField(
                    model_name="preorderreservation",
                    name="checkout_line",
                ),
                migrations.RemoveField(
                    model_name="preorderreservation",
                    name="product_variant_channel_listing",
                ),
                migrations.DeleteModel(name="PreorderAllocation"),
                migrations.DeleteModel(name="PreorderReservation"),
            ],
        )
    ]
