from uuid import uuid4

import pytest
from measurement.measures import Weight
from prices import Money, TaxedMoney

from saleor.checkout import calculations, utils
from saleor.checkout.models import Checkout
from saleor.checkout.utils import add_variant_to_checkout
from saleor.product.models import Category


@pytest.fixture()
def anonymous_checkout(db):
    return Checkout.objects.get_or_create(user=None)[0]


def test_get_or_create_user_checkout(
    customer_user, anonymous_checkout, user_checkout, admin_user
):
    checkout = utils.get_user_checkout(customer_user, auto_create=True)[0]
    assert Checkout.objects.all().count() == 2
    assert checkout == user_checkout

    # test against creating new checkouts
    Checkout.objects.create(user=admin_user)
    queryset = Checkout.objects.all()
    checkouts = list(queryset)
    checkout = utils.get_user_checkout(admin_user, auto_create=True)[0]
    assert Checkout.objects.all().count() == 3
    assert checkout in checkouts
    assert checkout.user == admin_user


def test_get_anonymous_checkout_from_token(anonymous_checkout, user_checkout):
    checkout = utils.get_anonymous_checkout_from_token(anonymous_checkout.token)
    assert Checkout.objects.all().count() == 2
    assert checkout == anonymous_checkout

    # test against new token
    checkout = utils.get_anonymous_checkout_from_token(uuid4())
    assert Checkout.objects.all().count() == 2
    assert checkout is None

    # test against getting checkout assigned to user
    checkout = utils.get_anonymous_checkout_from_token(user_checkout.token)
    assert Checkout.objects.all().count() == 2
    assert checkout is None


def test_get_user_checkout(
    anonymous_checkout, user_checkout, admin_user, customer_user
):
    checkout, created = utils.get_user_checkout(customer_user)
    assert Checkout.objects.all().count() == 2
    assert checkout == user_checkout
    assert not created


def test_adding_zero_quantity(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 0)
    assert checkout.lines.count() == 0


def test_adding_same_variant(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
    add_variant_to_checkout(checkout, variant, 2)
    assert checkout.lines.count() == 1
    assert checkout.quantity == 3
    subtotal = TaxedMoney(Money("30.00", "USD"), Money("30.00", "USD"))
    assert (
        calculations.checkout_subtotal(checkout=checkout, lines=list(checkout))
        == subtotal
    )


def test_replacing_same_variant(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1, replace=True)
    add_variant_to_checkout(checkout, variant, 2, replace=True)
    assert checkout.lines.count() == 1
    assert checkout.quantity == 2


def test_adding_invalid_quantity(checkout, product):
    variant = product.variants.get()
    with pytest.raises(ValueError):
        add_variant_to_checkout(checkout, variant, -1)


def test_getting_line(checkout, product):
    variant = product.variants.get()
    assert checkout.get_line(variant) is None
    add_variant_to_checkout(checkout, variant)
    assert checkout.lines.get() == checkout.get_line(variant)


def test_shipping_detection(checkout, product):
    assert not checkout.is_shipping_required()
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, replace=True)
    assert checkout.is_shipping_required()


def test_get_prices_of_discounted_specific_product(
    checkout_with_item, collection, voucher_specific_product_type
):
    checkout = checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    category = product.category

    product.collections.add(collection)
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)

    prices = utils.get_prices_of_discounted_specific_product(checkout, voucher)

    excepted_value = [line.variant.get_price() for item in range(line.quantity)]

    assert prices == excepted_value


def test_get_prices_of_discounted_specific_product_only_product(
    checkout_with_item, voucher_specific_product_type, product_with_default_variant
):
    checkout = checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    product2 = product_with_default_variant

    add_variant_to_checkout(checkout, product2.variants.get(), 1)
    voucher.products.add(product)

    prices = utils.get_prices_of_discounted_specific_product(checkout, voucher)

    excepted_value = [line.variant.get_price() for item in range(line.quantity)]

    assert checkout.lines.count() > 1
    assert prices == excepted_value


def test_get_prices_of_discounted_specific_product_only_collection(
    checkout_with_item,
    collection,
    voucher_specific_product_type,
    product_with_default_variant,
):
    checkout = checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    product2 = product_with_default_variant

    add_variant_to_checkout(checkout, product2.variants.get(), 1)
    product.collections.add(collection)
    voucher.collections.add(collection)

    prices = utils.get_prices_of_discounted_specific_product(checkout, voucher)

    excepted_value = [line.variant.get_price() for item in range(line.quantity)]

    assert checkout.lines.count() > 1
    assert prices == excepted_value


def test_get_prices_of_discounted_specific_product_only_category(
    checkout_with_item, voucher_specific_product_type, product_with_default_variant
):
    checkout = checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()
    product = line.variant.product
    product2 = product_with_default_variant
    category = product.category
    category2 = Category.objects.create(name="Cat", slug="cat")

    product2.category = category2
    product2.save()
    add_variant_to_checkout(checkout, product2.variants.get(), 1)
    voucher.categories.add(category)

    prices = utils.get_prices_of_discounted_specific_product(checkout, voucher)

    excepted_value = [line.variant.get_price() for item in range(line.quantity)]

    assert checkout.lines.count() > 1
    assert prices == excepted_value


def test_get_prices_of_discounted_specific_product_all_products(
    checkout_with_item, voucher_specific_product_type
):
    checkout = checkout_with_item
    voucher = voucher_specific_product_type
    line = checkout.lines.first()

    prices = utils.get_prices_of_discounted_specific_product(checkout, voucher)

    excepted_value = [line.variant.get_price() for item in range(line.quantity)]

    assert prices == excepted_value


def test_checkout_repr():
    checkout = Checkout()
    assert repr(checkout) == "Checkout(quantity=0)"

    checkout.quantity = 1
    assert repr(checkout) == "Checkout(quantity=1)"


def test_checkout_line_repr(product, checkout_with_single_item):
    variant = product.variants.get()
    line = checkout_with_single_item.lines.first()
    assert repr(line) == "CheckoutLine(variant=%r, quantity=%r)" % (
        variant,
        line.quantity,
    )


def test_checkout_line_state(product, checkout_with_single_item):
    variant = product.variants.get()
    line = checkout_with_single_item.lines.first()

    assert line.__getstate__() == (variant, line.quantity)

    line.__setstate__((variant, 2))

    assert line.quantity == 2


def test_get_total_weight(checkout_with_item):
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.weight = Weight(kg=10)
    variant.save()
    line.quantity = 6
    line.save()
    assert checkout_with_item.get_total_weight() == Weight(kg=60)
