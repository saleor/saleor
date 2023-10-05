from django.db.models import Exists, F, OuterRef

from ....celeryconf import app
from ....discount.models import Voucher, VoucherCode, VoucherCustomer
from ....product.models import (
    Product,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ....product.utils.variant_prices import update_discounted_prices_for_promotion

# For 100 rules, with 1000 variants for each rule it takes around 15s
PRICE_RECALCULATION_BATCH_SIZE = 100

# For 1 million vouchers it takes around 0.5s and consumes ~40MB memory at peak
VOUCHER_BATCH_SIZE = 5000

# The batch of size 1000 took about 0.2s
VOUCHER_CUSTOMER_BATCH_SIZE = 1000


@app.task
def update_discounted_prices_task():
    variant_listing_qs = (
        ProductVariantChannelListing.objects.annotate(
            discount=F("price_amount") - F("discounted_price_amount")
        )
        .filter(discount__gt=0)
        .filter(
            ~Exists(
                VariantChannelListingPromotionRule.objects.filter(
                    variant_channel_listing_id=OuterRef("id")
                )
            )
        )
    )
    variant_qs = ProductVariant.objects.filter(
        Exists(variant_listing_qs.filter(variant_id=OuterRef("id")))
    )
    products_ids = Product.objects.filter(
        Exists(variant_qs.filter(product_id=OuterRef("id")))
    ).values_list("id", flat=True)[:PRICE_RECALCULATION_BATCH_SIZE]
    if products_ids:
        products = Product.objects.filter(id__in=products_ids)
        update_discounted_prices_for_promotion(products)
        update_discounted_prices_task.delay()


@app.task
def move_codes_to_voucher_code_task():
    vouchers = Voucher.objects.filter(
        ~Exists(VoucherCode.objects.filter(voucher_id=OuterRef("id")))
    )
    if ids := vouchers.values_list("id", flat=True)[:VOUCHER_BATCH_SIZE]:
        qs = Voucher.objects.filter(id__in=ids)
        move_codes_to_voucher_code(qs)
        move_codes_to_voucher_code_task.delay()


def move_codes_to_voucher_code(vouchers):
    voucher_codes = []

    for voucher in vouchers.values("id", "code", "used"):
        voucher_codes.append(
            VoucherCode(
                voucher_id=voucher["id"],
                code=voucher["code"],
                used=voucher["used"],
            )
        )
    VoucherCode.objects.bulk_create(voucher_codes)


@app.task
def set_voucher_customer_codes_task():
    voucher_customers = VoucherCustomer.objects.exclude(
        Exists(VoucherCode.objects.filter(id=OuterRef("voucher_code_id")))
    ).order_by("pk")[:VOUCHER_CUSTOMER_BATCH_SIZE]
    if ids := list(voucher_customers.values_list("pk", flat=True)):
        qs = VoucherCustomer.objects.filter(pk__in=ids)
        set_voucher_code(qs)
        set_voucher_customer_codes_task.delay()


def set_voucher_code(voucher_customers):
    voucher_id_to_code_map = get_voucher_id_to_code_map(voucher_customers)
    voucher_customers_list = []
    for voucher_customer in voucher_customers:
        code = voucher_id_to_code_map[voucher_customer.voucher_id]
        voucher_customer.voucher_code = code
        voucher_customers_list.append(voucher_customer)
    VoucherCustomer.objects.bulk_update(voucher_customers_list, ["voucher_code"])


def get_voucher_id_to_code_map(voucher_customers):
    voucher_id_to_code_map = {}
    vouchers = Voucher.objects.filter(
        Exists(voucher_customers.filter(voucher_id=OuterRef("pk")))
    )
    codes = VoucherCode.objects.filter(
        Exists(vouchers.filter(id=OuterRef("voucher_id")))
    )
    for code in codes:
        voucher_id_to_code_map[code.voucher_id] = code

    return voucher_id_to_code_map
