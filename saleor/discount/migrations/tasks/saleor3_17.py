from django.db.models import Exists, F, OuterRef
from django.db import transaction

from ....celeryconf import app
from ....discount.models import (
    Voucher,
    VoucherCode,
    VoucherCustomer,
    CheckoutLineDiscount,
    OrderDiscount,
    OrderLineDiscount,
)
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


# The batch took about 0.2s and consumes ~20MB memory at peak
BASE_DISCOUNT_BATCH_SIZE = 1000


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
        with transaction.atomic():
            _vouchers = list(qs.select_for_update(of=(["self"])))
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
        with transaction.atomic():
            _voucher_customers = list(qs.select_for_update(of=(["self"])))
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


@app.task
def set_discounts_voucher_code_task():
    set_order_discount_voucher_code_task.delay()
    set_order_line_discount_voucher_code_task.delay()
    set_checkout_line_discount_voucher_code_task.delay()


@app.task
def set_order_discount_voucher_code_task() -> None:
    model_discounts = OrderDiscount.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")[:BASE_DISCOUNT_BATCH_SIZE]
    if ids := list(model_discounts.values_list("pk", flat=True)):
        qs = OrderDiscount.objects.filter(pk__in=ids)
        with transaction.atomic():
            _discounts = list(qs.select_for_update(of=(["self"])))
            set_discount_voucher_code(OrderDiscount, qs)
        set_order_discount_voucher_code_task.delay()


@app.task
def set_order_line_discount_voucher_code_task() -> None:
    model_discounts = OrderLineDiscount.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")[:BASE_DISCOUNT_BATCH_SIZE]
    if ids := list(model_discounts.values_list("pk", flat=True)):
        qs = OrderLineDiscount.objects.filter(pk__in=ids)
        with transaction.atomic():
            _discounts = list(qs.select_for_update(of=(["self"])))
            set_discount_voucher_code(OrderLineDiscount, qs)
        set_order_line_discount_voucher_code_task.delay()


@app.task
def set_checkout_line_discount_voucher_code_task() -> None:
    model_discounts = CheckoutLineDiscount.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")[:BASE_DISCOUNT_BATCH_SIZE]
    if ids := list(model_discounts.values_list("pk", flat=True)):
        qs = CheckoutLineDiscount.objects.filter(pk__in=ids)
        with transaction.atomic():
            _discounts = list(qs.select_for_update(of=(["self"])))
            set_discount_voucher_code(CheckoutLineDiscount, qs)
        set_checkout_line_discount_voucher_code_task.delay()


def set_discount_voucher_code(ModelDiscount, model_discounts) -> None:
    voucher_id_to_code_map = get_discount_voucher_id_to_code_map(model_discounts)
    model_discounts_list = []
    for model_discount in model_discounts:
        code = voucher_id_to_code_map[model_discount.voucher_id]
        model_discount.voucher_code = code
        model_discounts_list.append(model_discount)
    ModelDiscount.objects.bulk_update(model_discounts_list, ["voucher_code"])


def get_discount_voucher_id_to_code_map(model_discounts):
    vouchers = Voucher.objects.filter(
        Exists(model_discounts.filter(voucher_id=OuterRef("pk")))
    )
    voucher_id_to_code_map = {
        voucher_id: code for voucher_id, code in vouchers.values_list("id", "code")
    }
    return voucher_id_to_code_map
