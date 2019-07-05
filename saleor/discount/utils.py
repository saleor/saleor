import datetime
from collections import defaultdict
from typing import Iterable

from django.db.models import F
from django.utils.translation import pgettext

from ..core.taxes import zero_money
from ..extensions.manager import get_extensions_manager
from . import DiscountInfo
from .models import NotApplicable, Sale, VoucherCustomer


def increase_voucher_usage(voucher):
    """Increase voucher uses by 1."""
    voucher.used = F("used") + 1
    voucher.save(update_fields=["used"])


def decrease_voucher_usage(voucher):
    """Decrease voucher uses by 1."""
    voucher.used = F("used") - 1
    voucher.save(update_fields=["used"])


def add_voucher_usage_by_customer(voucher, customer_email):
    voucher_customer = VoucherCustomer.objects.filter(
        voucher=voucher, customer_email=customer_email
    )
    if voucher_customer:
        raise NotApplicable(
            pgettext(
                "Voucher not applicable",
                ("This offer is only valid once per customer."),
            )
        )
    VoucherCustomer.objects.create(voucher=voucher, customer_email=customer_email)


def remove_voucher_usage_by_customer(voucher, customer_email):
    voucher_customer = VoucherCustomer.objects.filter(
        voucher=voucher, customer_email=customer_email
    )
    if voucher_customer:
        voucher_customer.delete()


def are_product_collections_on_sale(product, discount: DiscountInfo):
    """Check if any collection is on sale."""
    discounted_collections = discount.collection_ids
    product_collections = set(c.id for c in product.collections.all())
    return product_collections.intersection(discounted_collections)


def get_product_discount_on_sale(product, discount: DiscountInfo):
    """Return discount value if product is on sale or raise NotApplicable."""
    is_product_on_sale = (
        product.id in discount.product_ids
        or product.category_id in discount.category_ids
        or are_product_collections_on_sale(product, discount)
    )
    if is_product_on_sale:
        return discount.sale.get_discount()
    raise NotApplicable(
        pgettext("Voucher not applicable", "Discount not applicable for this product")
    )


def get_product_discounts(product, discounts: Iterable[DiscountInfo]):
    """Return discount values for all discounts applicable to a product."""
    for discount in discounts:
        try:
            yield get_product_discount_on_sale(product, discount)
        except NotApplicable:
            pass


def calculate_discounted_price(product, price, discounts: Iterable[DiscountInfo]):
    """Return minimum product's price of all prices with discounts applied."""
    if discounts:
        discounts = list(get_product_discounts(product, discounts))
        if discounts:
            price = min(discount(price) for discount in discounts)
    return price


def validate_voucher_for_checkout(voucher, checkout, discounts):
    manager = get_extensions_manager()
    subtotal = manager.calculate_checkout_subtotal(checkout, discounts)
    customer_email = checkout.get_customer_email()
    validate_voucher(voucher, subtotal.gross, checkout.quantity, customer_email)


def validate_voucher_in_order(order):
    subtotal = order.get_subtotal()
    quantity = order.get_total_quantity()
    customer_email = order.get_customer_email()
    validate_voucher(order.voucher, subtotal.gross, quantity, customer_email)


def validate_voucher(voucher, total_price, quantity, customer_email):
    voucher.validate_min_amount_spent(total_price)
    voucher.validate_min_checkout_items_quantity(quantity)
    if voucher.apply_once_per_customer:
        voucher.validate_once_per_customer(customer_email)


def get_products_voucher_discount(voucher, prices):
    """Calculate discount value for a voucher of product or category type."""
    if voucher.apply_once_per_order:
        return voucher.get_discount_amount_for(min(prices))
    discounts = (voucher.get_discount_amount_for(price) for price in prices)
    total_amount = sum(discounts, zero_money())
    return total_amount


def _fetch_categories(sale_pks):
    from ..product.models import Category

    categories = Sale.categories.through.objects.filter(
        sale_id__in=sale_pks
    ).values_list("sale_id", "category_id")
    category_map = defaultdict(set)
    for sale_pk, category_pk in categories:
        category_map[sale_pk].add(category_pk)
    subcategory_map = defaultdict(set)
    for sale_pk, category_pks in category_map.items():
        subcategory_map[sale_pk] = set(
            Category.tree.filter(pk__in=category_pks)
            .get_descendants(include_self=True)
            .values_list("pk", flat=True)
        )
    return subcategory_map


def _fetch_collections(sale_pks):
    collections = Sale.collections.through.objects.filter(
        sale_id__in=sale_pks
    ).values_list("sale_id", "collection_id")
    collection_map = defaultdict(set)
    for sale_pk, collection_pk in collections:
        collection_map[sale_pk].add(collection_pk)
    return collection_map


def _fetch_products(sale_pks):
    products = Sale.products.through.objects.filter(sale_id__in=sale_pks).values_list(
        "sale_id", "product_id"
    )
    product_map = defaultdict(set)
    for sale_pk, product_pk in products:
        product_map[sale_pk].add(product_pk)
    return product_map


def fetch_discounts(date: datetime.date):
    sales = list(Sale.objects.active(date))
    pks = {s.pk for s in sales}
    collections = _fetch_collections(pks)
    products = _fetch_products(pks)
    categories = _fetch_categories(pks)

    return [
        DiscountInfo(
            sale=sale,
            category_ids=categories[sale.pk],
            collection_ids=collections[sale.pk],
            product_ids=products[sale.pk],
        )
        for sale in sales
    ]


def fetch_active_discounts():
    return fetch_discounts(datetime.date.today())
