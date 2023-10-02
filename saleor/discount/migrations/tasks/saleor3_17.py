from django.db.models import Exists, F, OuterRef

from ....celeryconf import app
from ....discount.models import Voucher, VoucherCode
from ....product.models import (
    Product,
    ProductVariant,
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ....product.utils.variant_prices import update_discounted_prices_for_promotion

# For 100 rules, with 1000 variants for each rule it takes around 15s
PRICE_RECALCULATION_BATCH_SIZE = 100

VOUCHER_BATCH_SIZE = 5000


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
