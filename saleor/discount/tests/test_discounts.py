from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from prices import Money

from ...checkout.utils import fetch_checkout_lines, get_voucher_discount_for_checkout
from ...plugins.manager import get_plugins_manager
from ...product.models import Product, ProductVariant, ProductVariantChannelListing
from .. import DiscountInfo, DiscountValueType, VoucherType
from ..models import (
    NotApplicable,
    Sale,
    SaleChannelListing,
    Voucher,
    VoucherChannelListing,
    VoucherCustomer,
)
from ..templatetags.voucher import discount_as_negative
from ..utils import (
    add_voucher_usage_by_customer,
    decrease_voucher_usage,
    get_product_discount_on_sale,
    increase_voucher_usage,
    remove_voucher_usage_by_customer,
    validate_voucher,
)


@pytest.mark.parametrize(
    "min_spent_amount, value",
    [(Money(5, "USD"), Money(10, "USD")), (Money(10, "USD"), Money(10, "USD"))],
)
def test_valid_voucher_min_spent_amount(min_spent_amount, value, channel_USD):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, "USD"),
        min_spent=min_spent_amount,
    )

    voucher.validate_min_spent(value, channel_USD)


def test_valid_voucher_min_spent_amount_voucher_not_assigned_to_channel(
    channel_USD, channel_PLN
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
        min_spent=(Money(5, channel_USD.currency_code)),
    )
    with pytest.raises(NotApplicable):
        voucher.validate_min_spent(Money(10, channel_PLN.currency_code), channel_PLN)


def test_valid_voucher_min_checkout_items_quantity(voucher):
    voucher.min_checkout_items_quantity = 3
    voucher.save()

    with pytest.raises(NotApplicable) as e:
        voucher.validate_min_checkout_items_quantity(2)

    assert (
        str(e.value)
        == "This offer is only valid for orders with a minimum of 3 quantity."
    )


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_variant_discounts(product, channel_USD):
    variant = product.variants.get()
    low_sale = Sale.objects.create(type=DiscountValueType.FIXED)
    low_sale_channel_listing = SaleChannelListing.objects.create(
        sale=low_sale,
        discount_value=5,
        currency=channel_USD.currency_code,
        channel=channel_USD,
    )
    low_discount = DiscountInfo(
        sale=low_sale,
        channel_listings={channel_USD.slug: low_sale_channel_listing},
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    sale = Sale.objects.create(type=DiscountValueType.FIXED)
    sale_channel_listing = SaleChannelListing.objects.create(
        sale=sale,
        discount_value=8,
        currency=channel_USD.currency_code,
        channel=channel_USD,
    )
    discount = DiscountInfo(
        sale=sale,
        channel_listings={channel_USD.slug: sale_channel_listing},
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    high_sale = Sale.objects.create(type=DiscountValueType.FIXED)
    high_sale_channel_listing = SaleChannelListing.objects.create(
        sale=high_sale,
        discount_value=50,
        currency=channel_USD.currency_code,
        channel=channel_USD,
    )
    high_discount = DiscountInfo(
        sale=high_sale,
        channel_listings={channel_USD.slug: high_sale_channel_listing},
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    final_price = variant.get_price(
        product,
        [],
        channel_USD,
        variant_channel_listing,
        discounts=[low_discount, discount, high_discount],
    )
    assert final_price == Money(0, "USD")


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product, channel_USD):
    variant = product.variants.get()
    sale = Sale.objects.create(type=DiscountValueType.PERCENTAGE)
    sale_channel_listing = SaleChannelListing.objects.create(
        sale=sale,
        discount_value=50,
        currency=channel_USD.currency_code,
        channel=channel_USD,
    )
    discount = DiscountInfo(
        sale=sale,
        channel_listings={channel_USD.slug: sale_channel_listing},
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    final_price = variant.get_price(
        product, [], channel_USD, variant_channel_listing, discounts=[discount]
    )
    assert final_price == Money(5, "USD")


def test_voucher_queryset_active(voucher, channel_USD):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active_in_channel(
        date=timezone.now() - timedelta(days=1), channel_slug=channel_USD.slug
    )
    assert active_vouchers.count() == 0


def test_voucher_queryset_active_in_channel(voucher, channel_USD):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active_in_channel(
        date=timezone.now(), channel_slug=channel_USD.slug
    )
    assert active_vouchers.count() == 1


def test_voucher_queryset_active_in_other_channel(voucher, channel_PLN):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active_in_channel(
        date=timezone.now(), channel_slug=channel_PLN.slug
    )
    assert active_vouchers.count() == 0


@pytest.mark.parametrize(
    "prices, discount_value, discount_type, apply_once_per_order, expected_value",
    [
        ([10], 10, DiscountValueType.FIXED, True, 10),
        ([5], 10, DiscountValueType.FIXED, True, 5),
        ([5, 5], 10, DiscountValueType.FIXED, True, 5),
        ([2, 3], 10, DiscountValueType.FIXED, True, 2),
        ([10, 10], 5, DiscountValueType.FIXED, False, 10),
        ([5, 2], 5, DiscountValueType.FIXED, False, 7),
        ([10, 10, 10], 5, DiscountValueType.FIXED, False, 15),
    ],
)
def test_specific_products_voucher_checkout_discount(
    monkeypatch,
    prices,
    discount_value,
    discount_type,
    expected_value,
    apply_once_per_order,
    checkout_with_item,
    channel_USD,
):
    discounts = []
    monkeypatch.setattr(
        "saleor.checkout.utils.get_prices_of_discounted_specific_product",
        lambda manager, checkout, lines, voucher, channel, discounts: (
            Money(price, "USD") for price in prices
        ),
    )
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        apply_once_per_order=apply_once_per_order,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    checkout = checkout_with_item
    lines = fetch_checkout_lines(checkout)
    manager = get_plugins_manager()
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout, lines, checkout.shipping_address, discounts
    )
    assert discount == Money(expected_value, "USD")


def test_sale_applies_to_correct_products(product_type, category, channel_USD):
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="",
        pk=111,
        product_type=product_type,
        category=category,
    )
    variant = ProductVariant.objects.create(product=product, sku="firstvar")
    variant_channel_listing = ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    product2 = Product.objects.create(
        name="Second product",
        slug="second-product",
        description="",
        product_type=product_type,
        category=category,
    )
    sec_variant = ProductVariant.objects.create(product=product2, sku="secvar", pk=111)
    ProductVariantChannelListing.objects.create(
        variant=sec_variant,
        channel=channel_USD,
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    sale = Sale.objects.create(name="Test sale", type=DiscountValueType.FIXED)
    sale_channel_listing = SaleChannelListing.objects.create(
        sale=sale,
        currency=channel_USD.currency_code,
        channel=channel_USD,
        discount_value=3,
    )
    discount = DiscountInfo(
        sale=sale,
        channel_listings={channel_USD.slug: sale_channel_listing},
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    product_discount = get_product_discount_on_sale(
        variant.product, set(), discount, channel_USD
    )

    discounted_price = product_discount(variant_channel_listing.price)
    assert discounted_price == Money(7, "USD")
    with pytest.raises(NotApplicable):
        get_product_discount_on_sale(sec_variant.product, set(), discount, channel_USD)


def test_increase_voucher_usage(channel_USD):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.FIXED,
        usage_limit=100,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    increase_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 1


def test_decrease_voucher_usage(channel_USD):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.FIXED,
        usage_limit=100,
        used=10,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    decrease_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 9


def test_add_voucher_usage_by_customer(voucher, customer_user):
    voucher_customer_count = VoucherCustomer.objects.all().count()
    add_voucher_usage_by_customer(voucher, customer_user.email)
    assert VoucherCustomer.objects.all().count() == voucher_customer_count + 1
    voucherCustomer = VoucherCustomer.objects.first()
    assert voucherCustomer.voucher == voucher
    assert voucherCustomer.customer_email == customer_user.email


def test_add_voucher_usage_by_customer_raise_not_applicable(voucher_customer):
    voucher = voucher_customer.voucher
    customer_email = voucher_customer.customer_email
    with pytest.raises(NotApplicable):
        add_voucher_usage_by_customer(voucher, customer_email)


def test_remove_voucher_usage_by_customer(voucher_customer):
    voucher_customer_count = VoucherCustomer.objects.all().count()
    voucher = voucher_customer.voucher
    customer_email = voucher_customer.customer_email
    remove_voucher_usage_by_customer(voucher, customer_email)
    assert VoucherCustomer.objects.all().count() == voucher_customer_count - 1


def test_remove_voucher_usage_by_customer_not_exists(voucher):
    remove_voucher_usage_by_customer(voucher, "fake@exmaimpel.com")


@pytest.mark.parametrize(
    "total, min_spent_amount, total_quantity, min_checkout_items_quantity,"
    "discount_value_type",
    [
        (20, 20, 2, 2, DiscountValueType.PERCENTAGE),
        (20, None, 2, None, DiscountValueType.PERCENTAGE),
        (20, 20, 2, 2, DiscountValueType.FIXED),
        (20, None, 2, None, DiscountValueType.FIXED),
    ],
)
def test_validate_voucher(
    total,
    min_spent_amount,
    total_quantity,
    min_checkout_items_quantity,
    discount_value_type,
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
        min_spent_amount=min_spent_amount,
    )
    total_price = Money(total, "USD")
    validate_voucher(
        voucher, total_price, total_quantity, "test@example.com", channel_USD
    )


@pytest.mark.parametrize(
    "total, min_spent_amount, total_quantity, min_checkout_items_quantity, "
    "discount_value, discount_value_type",
    [
        (20, 50, 2, 10, 50, DiscountValueType.PERCENTAGE),
        (20, 50, 2, None, 50, DiscountValueType.PERCENTAGE),
        (20, None, 2, 10, 50, DiscountValueType.FIXED),
    ],
)
def test_validate_voucher_not_applicable(
    total,
    min_spent_amount,
    total_quantity,
    min_checkout_items_quantity,
    discount_value,
    discount_value_type,
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
        min_spent_amount=min_spent_amount,
    )
    total_price = Money(total, "USD")
    with pytest.raises(NotApplicable):
        validate_voucher(
            voucher, total_price, total_quantity, "test@example.com", channel_USD
        )


def test_validate_voucher_not_applicable_once_per_customer(
    voucher, customer_user, channel_USD
):
    voucher.apply_once_per_customer = True
    voucher.save()
    VoucherCustomer.objects.create(voucher=voucher, customer_email=customer_user.email)
    with pytest.raises(NotApplicable):
        validate_voucher(voucher, 0, 0, customer_user.email, channel_USD)


date_time_now = timezone.now()


@pytest.mark.parametrize(
    "current_date, start_date, end_date, is_active",
    (
        (date_time_now, date_time_now, date_time_now + timedelta(days=1), True),
        (
            date_time_now + timedelta(days=1),
            date_time_now,
            date_time_now + timedelta(days=1),
            True,
        ),
        (
            date_time_now + timedelta(days=2),
            date_time_now,
            date_time_now + timedelta(days=1),
            False,
        ),
        (
            date_time_now - timedelta(days=2),
            date_time_now,
            date_time_now + timedelta(days=1),
            False,
        ),
        (date_time_now, date_time_now, None, True),
        (date_time_now + timedelta(weeks=10), date_time_now, None, True),
    ),
)
def test_sale_active(current_date, start_date, end_date, is_active, channel_USD):
    sale = Sale.objects.create(
        type=DiscountValueType.FIXED, start_date=start_date, end_date=end_date
    )
    SaleChannelListing.objects.create(
        sale=sale,
        currency=channel_USD.currency_code,
        channel=channel_USD,
        discount_value=5,
    )
    sale_is_active = Sale.objects.active(date=current_date).exists()
    assert is_active == sale_is_active


def test_discount_as_negative():
    discount = Money(10, "USD")
    result = discount_as_negative(discount)
    assert result == "-$10.00"


def test_discount_as_negative_for_zero_value():
    discount = Money(0, "USD")
    result = discount_as_negative(discount)
    assert result == "$0.00"


def test_discount_as_negative_for_html():
    discount = Money(10, "USD")
    result = discount_as_negative(discount, True)
    assert result == '-<span class="currency">$</span>10.00'


def test_get_fixed_sale_discount(sale):
    # given
    sale.type = DiscountValueType.FIXED
    channel_listing = sale.channel_listings.get()

    # when
    result = sale.get_discount(channel_listing).keywords

    # then
    assert result["discount"] == Money(
        channel_listing.discount_value, channel_listing.currency
    )


def test_get_percentage_sale_discount(sale):
    # given
    sale.type = DiscountValueType.PERCENTAGE
    channel_listing = sale.channel_listings.get()

    # when
    result = sale.get_discount(channel_listing).keywords

    # then
    assert result["percentage"] == channel_listing.discount_value


def test_get_unknown_sale_discount(sale):
    sale.type = "unknown"
    channel_listing = sale.channel_listings.get()

    with pytest.raises(NotImplementedError):
        sale.get_discount(channel_listing)


def test_get_not_applicable_sale_discount(sale, channel_PLN):
    sale.type = DiscountValueType.PERCENTAGE

    with pytest.raises(NotApplicable):
        sale.get_discount(None)
