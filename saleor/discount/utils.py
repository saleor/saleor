import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Set

from django.db.models import F
from django.utils import timezone
from prices import Money

from ..channel.models import Channel
from ..checkout import calculations
from ..core.taxes import zero_money
from . import DiscountInfo
from .models import NotApplicable, Sale, SaleChannelListing, VoucherCustomer

if TYPE_CHECKING:
    # flake8: noqa
    from ..checkout import CheckoutLineInfo
    from ..checkout.models import Checkout
    from ..order.models import Order
    from ..plugins.manager import PluginsManager
    from ..product.models import Collection, Product
    from .models import Voucher


def increase_voucher_usage(voucher: "Voucher") -> None:
    """Increase voucher uses by 1."""
    voucher.used = F("used") + 1
    voucher.save(update_fields=["used"])


def decrease_voucher_usage(voucher: "Voucher") -> None:
    """Decrease voucher uses by 1."""
    voucher.used = F("used") - 1
    voucher.save(update_fields=["used"])


def add_voucher_usage_by_customer(voucher: "Voucher", customer_email: str) -> None:
    voucher_customer = VoucherCustomer.objects.filter(
        voucher=voucher, customer_email=customer_email
    )
    if voucher_customer:
        raise NotApplicable("This offer is only valid once per customer.")
    VoucherCustomer.objects.create(voucher=voucher, customer_email=customer_email)


def remove_voucher_usage_by_customer(voucher: "Voucher", customer_email: str) -> None:
    voucher_customer = VoucherCustomer.objects.filter(
        voucher=voucher, customer_email=customer_email
    )
    if voucher_customer:
        voucher_customer.delete()


def get_product_discount_on_sale(
    product: "Product",
    product_collections: Set[int],
    discount: DiscountInfo,
    channel: "Channel",
):
    """Return discount value if product is on sale or raise NotApplicable."""
    is_product_on_sale = (
        product.id in discount.product_ids
        or product.category_id in discount.category_ids
        or product_collections.intersection(discount.collection_ids)
    )
    if is_product_on_sale:
        sale_channel_listing = discount.channel_listings.get(channel.slug)
        return discount.sale.get_discount(sale_channel_listing)  # type: ignore
    raise NotApplicable("Discount not applicable for this product")


def get_product_discounts(
    *,
    product: "Product",
    collections: Iterable["Collection"],
    discounts: Iterable[DiscountInfo],
    channel: "Channel"
) -> Money:
    """Return discount values for all discounts applicable to a product."""
    product_collections = set(pc.id for pc in collections)
    for discount in discounts or []:
        try:
            yield get_product_discount_on_sale(
                product, product_collections, discount, channel
            )
        except NotApplicable:
            pass


def calculate_discounted_price(
    *,
    product: "Product",
    price: Money,
    collections: Iterable["Collection"],
    discounts: Optional[Iterable[DiscountInfo]],
    channel: "Channel"
) -> Money:
    """Return minimum product's price of all prices with discounts applied."""
    if discounts:
        discount_prices = list(
            get_product_discounts(
                product=product,
                collections=collections,
                discounts=discounts,
                channel=channel,
            )
        )
        if discount_prices:
            price = min(discount(price) for discount in discount_prices)
    return price


def validate_voucher_for_checkout(
    manager: "PluginsManager",
    voucher: "Voucher",
    checkout: "Checkout",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Optional[Iterable[DiscountInfo]],
):
    address = checkout.shipping_address or checkout.billing_address
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=address,
        discounts=discounts,
    )

    customer_email = checkout.get_customer_email()
    validate_voucher(
        voucher,
        subtotal.gross,
        checkout.quantity,
        customer_email,
        checkout.channel,
    )


def validate_voucher_in_order(order: "Order"):
    subtotal = order.get_subtotal()
    quantity = order.get_total_quantity()
    customer_email = order.get_customer_email()
    if not order.voucher:
        return
    validate_voucher(
        order.voucher, subtotal.gross, quantity, customer_email, order.channel
    )


def validate_voucher(
    voucher: "Voucher",
    total_price: Money,
    quantity: int,
    customer_email: str,
    channel: Channel,
) -> None:
    voucher.validate_min_spent(total_price, channel)
    voucher.validate_min_checkout_items_quantity(quantity)
    if voucher.apply_once_per_customer:
        voucher.validate_once_per_customer(customer_email)


def get_products_voucher_discount(
    voucher: "Voucher", prices: Iterable[Money], channel: Channel
) -> Money:
    """Calculate discount value for a voucher of product or category type."""
    if voucher.apply_once_per_order:
        return voucher.get_discount_amount_for(min(prices), channel)
    discounts = (voucher.get_discount_amount_for(price, channel) for price in prices)
    total_amount = sum(discounts, zero_money(channel.currency_code))
    return total_amount


def fetch_categories(sale_pks: Iterable[str]) -> Dict[int, Set[int]]:
    from ..product.models import Category

    categories = (
        Sale.categories.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "category_id")
    )
    category_map: Dict[int, Set[int]] = defaultdict(set)
    for sale_pk, category_pk in categories:
        category_map[sale_pk].add(category_pk)
    subcategory_map: Dict[int, Set[int]] = defaultdict(set)
    for sale_pk, category_pks in category_map.items():
        subcategory_map[sale_pk] = set(
            Category.tree.filter(pk__in=category_pks)
            .get_descendants(include_self=True)
            .values_list("pk", flat=True)
        )
    return subcategory_map


def fetch_collections(sale_pks: Iterable[str]) -> Dict[int, Set[int]]:
    collections = (
        Sale.collections.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "collection_id")
    )
    collection_map: Dict[int, Set[int]] = defaultdict(set)
    for sale_pk, collection_pk in collections:
        collection_map[sale_pk].add(collection_pk)
    return collection_map


def fetch_products(sale_pks: Iterable[str]) -> Dict[int, Set[int]]:
    products = (
        Sale.products.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "product_id")
    )
    product_map: Dict[int, Set[int]] = defaultdict(set)
    for sale_pk, product_pk in products:
        product_map[sale_pk].add(product_pk)
    return product_map


def fetch_sale_channel_listings(
    sale_pks: Iterable[str],
):
    channel_listings = SaleChannelListing.objects.filter(sale_id__in=sale_pks).annotate(
        channel_slug=F("channel__slug")
    )
    channel_listings_map: Dict[int, Dict[str, SaleChannelListing]] = defaultdict(dict)
    for channel_listing in channel_listings:
        sale_id_row = channel_listings_map[channel_listing.sale_id]
        sale_id_row[channel_listing.channel_slug] = channel_listing
    return channel_listings_map


def fetch_discounts(date: datetime.date) -> List[DiscountInfo]:
    sales = list(Sale.objects.active(date))
    pks = {s.pk for s in sales}
    collections = fetch_collections(pks)
    channel_listings = fetch_sale_channel_listings(pks)
    products = fetch_products(pks)
    categories = fetch_categories(pks)

    return [
        DiscountInfo(
            sale=sale,
            category_ids=categories[sale.pk],
            channel_listings=channel_listings[sale.pk],
            collection_ids=collections[sale.pk],
            product_ids=products[sale.pk],
        )
        for sale in sales
    ]


def fetch_active_discounts() -> List[DiscountInfo]:
    return fetch_discounts(timezone.now())
