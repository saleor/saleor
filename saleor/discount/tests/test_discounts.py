from datetime import timedelta

import pytest
from django.utils import timezone
from prices import Money

from saleor.checkout.utils import get_voucher_discount_for_checkout
from saleor.discount import DiscountInfo, DiscountValueType, VoucherType
from saleor.discount.models import NotApplicable, Sale, Voucher, VoucherCustomer
from saleor.discount.templatetags.voucher import discount_as_negative
from saleor.discount.utils import (
    add_voucher_usage_by_customer,
    decrease_voucher_usage,
    get_product_discount_on_sale,
    increase_voucher_usage,
    remove_voucher_usage_by_customer,
    validate_voucher,
)
from saleor.product.models import Product, ProductVariant


@pytest.mark.parametrize(
    "min_spent_amount, value",
    [(Money(5, "USD"), Money(10, "USD")), (Money(10, "USD"), Money(10, "USD"))],
)
def test_valid_voucher_min_spent_amount(min_spent_amount, value):
    voucher = Voucher(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
        discount=Money(10, "USD"),
        min_spent=min_spent_amount,
    )
    voucher.validate_min_spent(value)


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
def test_variant_discounts(product):
    variant = product.variants.get()
    low_sale = Sale(type=DiscountValueType.FIXED, value=5)
    low_discount = DiscountInfo(
        sale=low_sale,
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    sale = Sale(type=DiscountValueType.FIXED, value=8)
    discount = DiscountInfo(
        sale=sale, product_ids={product.id}, category_ids=set(), collection_ids=set()
    )
    high_sale = Sale(type=DiscountValueType.FIXED, value=50)
    high_discount = DiscountInfo(
        sale=high_sale,
        product_ids={product.id},
        category_ids=set(),
        collection_ids=set(),
    )
    final_price = variant.get_price(discounts=[low_discount, discount, high_discount])
    assert final_price == Money(0, "USD")


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_percentage_discounts(product):
    variant = product.variants.get()
    sale = Sale(type=DiscountValueType.PERCENTAGE, value=50)
    discount = DiscountInfo(
        sale=sale, product_ids={product.id}, category_ids=set(), collection_ids={}
    )
    final_price = variant.get_price(discounts=[discount])
    assert final_price == Money(5, "USD")


def test_voucher_queryset_active(voucher):
    vouchers = Voucher.objects.all()
    assert vouchers.count() == 1
    active_vouchers = Voucher.objects.active(date=timezone.now() - timedelta(days=1))
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
):
    discounts = []
    monkeypatch.setattr(
        "saleor.checkout.utils.get_prices_of_discounted_specific_product",
        lambda lines, discounts, discounted_products: (
            Money(price, "USD") for price in prices
        ),
    )
    voucher = Voucher(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_once_per_order=apply_once_per_order,
    )
    voucher.save()
    checkout = checkout_with_item
    discount = get_voucher_discount_for_checkout(
        voucher, checkout, list(checkout), discounts
    )
    assert discount == Money(expected_value, "USD")


def test_sale_applies_to_correct_products(product_type, category):
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        price=Money(10, "USD"),
        description="",
        pk=111,
        product_type=product_type,
        category=category,
    )
    variant = ProductVariant.objects.create(product=product, sku="firstvar")
    product2 = Product.objects.create(
        name="Second product",
        slug="second-product",
        price=Money(15, "USD"),
        description="",
        product_type=product_type,
        category=category,
    )
    sec_variant = ProductVariant.objects.create(product=product2, sku="secvar", pk=111)
    sale = Sale(name="Test sale", value=3, type=DiscountValueType.FIXED)
    discount = DiscountInfo(
        sale=sale, product_ids={product.id}, category_ids=set(), collection_ids=set()
    )
    product_discount = get_product_discount_on_sale(variant.product, set(), discount)
    discounted_price = product_discount(product.price)
    assert discounted_price == Money(7, "USD")
    with pytest.raises(NotApplicable):
        get_product_discount_on_sale(sec_variant.product, set(), discount)


def test_increase_voucher_usage():
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        usage_limit=100,
    )
    increase_voucher_usage(voucher)
    voucher.refresh_from_db()
    assert voucher.used == 1


def test_decrease_voucher_usage():
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        usage_limit=100,
        used=10,
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
):
    voucher = Voucher.objects.create(
        code="unique",
        currency="USD",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        discount_value=50,
        min_spent_amount=min_spent_amount,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    total_price = Money(total, "USD")
    validate_voucher(voucher, total_price, total_quantity, "test@example.com")


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
):
    voucher = Voucher.objects.create(
        code="unique",
        currency="USD",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        discount_value=discount_value,
        min_spent_amount=min_spent_amount,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    total_price = Money(total, "USD")
    with pytest.raises(NotApplicable):
        validate_voucher(voucher, total_price, total_quantity, "test@example.com")


def test_validate_voucher_not_applicable_once_per_customer(voucher, customer_user):
    voucher.apply_once_per_customer = True
    voucher.save()
    VoucherCustomer.objects.create(voucher=voucher, customer_email=customer_user.email)
    with pytest.raises(NotApplicable):
        validate_voucher(voucher, 0, 0, customer_user.email)


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
def test_sale_active(current_date, start_date, end_date, is_active):
    Sale.objects.create(
        type=DiscountValueType.FIXED, value=5, start_date=start_date, end_date=end_date
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
