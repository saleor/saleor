from django.db import migrations
from django.db.models import Exists, OuterRef


# For batch size 1000 with 10_000 per model OrderDiscount/Voucher/VoucherCode objects
# OrderDiscount Migration took 2.39 seconds.
# OrderDiscount Memory usage increased by 15.65 MiB.
# OrderLineDiscount Migration took 2.48 seconds.
# OrderLineDiscount Memory usage increased by 4.61 MiB.
# CheckoutLineDiscount Migration took 2.26 seconds.
# CheckoutLineDiscount Memory usage increased by 3.23 MiB.

# For batch size 1000 with 100_000 per model OrderDiscount/Voucher/VoucherCode objects
# OrderDiscount Migration took 28.68 seconds.
# OrderDiscount Memory usage increased by 163.00 MiB.
# OrderLineDiscount Migration took 27.98 seconds.
# OrderLineDiscount Memory usage increased by 47.99 MiB.
# CheckoutLineDiscount Migration took 28.12 seconds.
# CheckoutLineDiscount Memory usage increased by 35.52 MiB.


BATCH_SIZE = 1000


def set_voucher_code_in_model(ModelName, apps, schema_editor):
    ModelDiscount = apps.get_model("discount", ModelName)
    Voucher = apps.get_model("discount", "Voucher")
    VoucherCode = apps.get_model("discount", "VoucherCode")
    set_voucher_to_voucher_code(ModelDiscount, Voucher, VoucherCode)


def set_voucher_to_voucher_code(ModelDiscount, Voucher, VoucherCode) -> None:
    model_discounts = ModelDiscount.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")[:BATCH_SIZE]
    if ids := list(model_discounts.values_list("pk", flat=True)):
        qs = ModelDiscount.objects.filter(pk__in=ids)
        set_voucher_code(ModelDiscount, Voucher, VoucherCode, qs)
        set_voucher_to_voucher_code(ModelDiscount, Voucher, VoucherCode)


def set_voucher_code(ModelDiscount, Voucher, VoucherCode, model_discounts) -> None:
    voucher_id_to_code_map = get_voucher_id_to_code_map(
        Voucher, VoucherCode, model_discounts
    )
    model_discounts_list = []
    for model_discount in model_discounts:
        code = voucher_id_to_code_map[model_discount.voucher_id]
        model_discount.voucher_code = code
        model_discounts_list.append(model_discount)
    ModelDiscount.objects.bulk_update(model_discounts_list, ["voucher_code"])


def get_voucher_id_to_code_map(Voucher, VoucherCode, model_discounts) -> None:
    voucher_id_to_code_map = {}
    vouchers = Voucher.objects.filter(
        Exists(model_discounts.filter(voucher_id=OuterRef("pk")))
    )
    codes = VoucherCode.objects.filter(
        Exists(vouchers.filter(id=OuterRef("voucher_id")))
    )
    for code in codes:
        voucher_id_to_code_map[code.voucher_id] = code.code

    return voucher_id_to_code_map


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0066_basediscount_voucher_code_add_index"),
    ]

    operations = [
        migrations.RunPython(
            lambda apps, schema_editor: set_voucher_code_in_model(
                "OrderDiscount", apps, schema_editor
            ),
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            lambda apps, schema_editor: set_voucher_code_in_model(
                "OrderLineDiscount", apps, schema_editor
            ),
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            lambda apps, schema_editor: set_voucher_code_in_model(
                "CheckoutLineDiscount", apps, schema_editor
            ),
            migrations.RunPython.noop,
        ),
    ]
