from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from prices import Money, TaxedMoney

from ...product.models import Product, ProductVariant, ProductVariantChannelListing
from .. import DiscountInfo, DiscountValueType, RewardValueType, VoucherType
from ..models import (
    NotApplicable,
    Sale,
    SaleChannelListing,
    Voucher,
    VoucherChannelListing,
    VoucherCustomer,
)
from ..utils import (
    add_voucher_usage_by_customer,
    decrease_voucher_usage,
    fetch_catalogue_info,
    get_product_discount_on_sale,
    increase_voucher_usage,
    remove_voucher_usage_by_customer,
    validate_voucher,
)


def test_valid_voucher_min_spent_amount(channel_USD):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, "USD"),
        min_spent=Money(7, "USD"),
    )
    value = Money(7, "USD")

    voucher.validate_min_spent(value, channel_USD)


def test_valid_voucher_min_spent_amount_not_reached(channel_USD):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, "USD"),
        min_spent=Money(7, "USD"),
    )
    value = Money(5, "USD")

    with pytest.raises(NotApplicable):
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
    price = Money(10, channel_PLN.currency_code)
    total_price = TaxedMoney(net=price, gross=price)
    with pytest.raises(NotApplicable):
        voucher.validate_min_spent(total_price, channel_PLN)


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
def test_percentage_discounts(product, channel_USD, promotion_without_rules):
    # given
    variant = product.variants.get()
    reward_value = Decimal("50")
    rule = promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=Decimal("5"),
        currency=channel_USD.currency_code,
    )
    price = Decimal("10")

    # when
    final_price = variant.get_price(variant_channel_listing, price)

    # then
    assert final_price.amount == price - reward_value / 100 * price


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_fixed_discounts(product, channel_USD, promotion_without_rules):
    # given
    variant = product.variants.get()
    reward_value = Decimal("5")
    rule = promotion_without_rules.rules.create(
        catalogue_predicate={
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", variant.product.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_channel_listing.variantlistingpromotionrule.create(
        promotion_rule=rule,
        discount_amount=Decimal("1"),
        currency=channel_USD.currency_code,
    )
    price = Decimal("10")

    # when
    final_price = variant.get_price(variant_channel_listing, price)

    # then
    assert final_price.amount == price - reward_value


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


def test_sale_applies_to_correct_products(product_type, category, channel_USD):
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description={},
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
        description={},
        product_type=product_type,
        category=category,
    )
    sec_variant = ProductVariant.objects.create(product=product2, sku="secvar")
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
        variants_ids=set(),
    )
    _, product_discount = get_product_discount_on_sale(
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
        voucher, total_price, total_quantity, "test@example.com", channel_USD, None
    )


def test_validate_staff_voucher_for_anonymous(
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.PERCENTAGE,
        only_for_staff=True,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )
    total_price = Money(100, "USD")
    price = TaxedMoney(gross=total_price, net=total_price)
    with pytest.raises(NotApplicable):
        validate_voucher(voucher, price, 2, "test@example.com", channel_USD, None)


def test_validate_staff_voucher_for_normal_customer(channel_USD, customer_user):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.PERCENTAGE,
        only_for_staff=True,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )
    total_price = Money(100, "USD")
    price = TaxedMoney(gross=total_price, net=total_price)
    with pytest.raises(NotApplicable):
        validate_voucher(
            voucher, price, 2, customer_user.email, channel_USD, customer_user
        )


def test_validate_staff_voucher_for_staff_customer(channel_USD, staff_user):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.PERCENTAGE,
        only_for_staff=True,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )
    total_price = Money(100, "USD")
    price = TaxedMoney(gross=total_price, net=total_price)

    validate_voucher(voucher, price, 2, staff_user.email, channel_USD, staff_user)


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
            voucher, total_price, total_quantity, "test@example.com", channel_USD, None
        )


def test_validate_voucher_not_applicable_once_per_customer(
    voucher, customer_user, channel_USD
):
    voucher.apply_once_per_customer = True
    voucher.save()
    VoucherCustomer.objects.create(voucher=voucher, customer_email=customer_user.email)
    price = Money(0, "USD")
    total_price = TaxedMoney(net=price, gross=price)
    with pytest.raises(NotApplicable):
        validate_voucher(
            voucher,
            total_price,
            0,
            customer_user.email,
            channel_USD,
            customer_user,
        )


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


def test_fetch_catalogue_info_for_sale_has_one_element_sets(sale):
    category_ids = set(sale.categories.all().values_list("id", flat=True))
    collection_ids = set(sale.collections.all().values_list("id", flat=True))
    product_ids = set(sale.products.all().values_list("id", flat=True))
    variant_ids = set(sale.variants.all().values_list("id", flat=True))

    catalogue_info = fetch_catalogue_info(sale)

    assert catalogue_info["categories"]
    assert catalogue_info["collections"]
    assert catalogue_info["products"]
    assert catalogue_info["variants"]

    assert catalogue_info["categories"] == category_ids
    assert catalogue_info["collections"] == collection_ids
    assert catalogue_info["products"] == product_ids
    assert catalogue_info["variants"] == variant_ids
