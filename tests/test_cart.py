from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest
from measurement.measures import Weight
from prices import Money, TaxedMoney

from saleor.checkout import calculations, forms, utils
from saleor.checkout.context_processors import checkout_counter
from saleor.checkout.models import Checkout
from saleor.checkout.utils import (
    add_variant_to_checkout,
    change_checkout_user,
    find_open_checkout_for_user,
    get_shipping_price_estimate,
)
from saleor.core.exceptions import InsufficientStock
from saleor.product.models import Category


@pytest.fixture()
def anonymous_checkout(db):
    return Checkout.objects.get_or_create(user=None)[0]


def test_get_or_create_anonymous_checkout_from_token(anonymous_checkout, user_checkout):
    queryset = Checkout.objects.all()
    checkouts = list(queryset)
    checkout = utils.get_or_create_anonymous_checkout_from_token(
        anonymous_checkout.token
    )
    assert Checkout.objects.all().count() == 2
    assert checkout == anonymous_checkout

    # test against new token
    checkout = utils.get_or_create_anonymous_checkout_from_token(uuid4())
    assert Checkout.objects.all().count() == 3
    assert checkout not in checkouts
    assert checkout.user is None
    checkout.delete()

    # test against getting checkout assigned to user
    checkout = utils.get_or_create_anonymous_checkout_from_token(user_checkout.token)
    assert Checkout.objects.all().count() == 3
    assert checkout not in checkouts
    assert checkout.user is None


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
    assert len(checkout) == 0


def test_adding_same_variant(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
    add_variant_to_checkout(checkout, variant, 2)
    assert len(checkout) == 1
    assert checkout.quantity == 3
    subtotal = TaxedMoney(Money("30.00", "USD"), Money("30.00", "USD"))
    assert calculations.checkout_subtotal(checkout) == subtotal


def test_replacing_same_variant(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1, replace=True)
    add_variant_to_checkout(checkout, variant, 2, replace=True)
    assert len(checkout) == 1
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


def test_checkout_counter(monkeypatch):
    monkeypatch.setattr(
        "saleor.checkout.context_processors.get_checkout_from_request",
        Mock(return_value=Mock(quantity=4)),
    )
    ret = checkout_counter(Mock())
    assert ret == {"checkout_counter": 4}


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


def test_contains_unavailable_variants():
    missing_variant = Mock(check_quantity=Mock(side_effect=InsufficientStock("")))
    checkout = MagicMock()
    checkout.__iter__ = Mock(return_value=iter([Mock(variant=missing_variant)]))
    assert utils.contains_unavailable_variants(checkout)

    variant = Mock(check_quantity=Mock())
    checkout.__iter__ = Mock(return_value=iter([Mock(variant=variant)]))
    assert not utils.contains_unavailable_variants(checkout)


def test_remove_unavailable_variants(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant)
    variant.quantity = 0
    variant.save()
    utils.remove_unavailable_variants(checkout)
    assert len(checkout) == 0


def test_check_product_availability_and_warn(monkeypatch, checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant)
    monkeypatch.setattr("django.contrib.messages.warning", Mock(warning=Mock()))
    monkeypatch.setattr(
        "saleor.checkout.utils.contains_unavailable_variants", Mock(return_value=False)
    )

    utils.check_product_availability_and_warn(MagicMock(), checkout)
    assert len(checkout) == 1

    monkeypatch.setattr(
        "saleor.checkout.utils.contains_unavailable_variants", Mock(return_value=True)
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.remove_unavailable_variants",
        lambda c: add_variant_to_checkout(checkout, variant, 0, replace=True),
    )

    utils.check_product_availability_and_warn(MagicMock(), checkout)
    assert len(checkout) == 0


def test_add_to_checkout_form(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    data = {"quantity": 1}
    form = forms.AddToCheckoutForm(data=data, checkout=checkout, product=product)

    form.get_variant = Mock(return_value=variant)

    assert form.is_valid()
    form.save()
    assert checkout.lines.count() == 1
    assert checkout.lines.filter(variant=variant).exists()

    with pytest.raises(NotImplementedError):
        data = {"quantity": 1}
        form = forms.AddToCheckoutForm(data=data, checkout=checkout, product=product)
        form.is_valid()
    data = {}

    form = forms.AddToCheckoutForm(data=data, checkout=checkout, product=product)
    assert not form.is_valid()


@pytest.mark.parametrize("track_inventory", (True, False))
def test_add_to_checkout_form_when_insufficient_stock(product, track_inventory):
    variant = product.variants.first()
    variant.track_inventory = track_inventory
    variant.save()

    checkout_lines = []
    checkout = Mock(
        add=lambda variant, quantity: checkout_lines.append(variant),
        get_line=Mock(return_value=Mock(quantity=49)),
    )

    form = forms.AddToCheckoutForm(
        data={"quantity": 1}, checkout=checkout, product=Mock()
    )
    form.get_variant = Mock(return_value=variant)

    if track_inventory:
        assert not form.is_valid()
    else:
        assert form.is_valid()


def test_replace_checkout_line_form(checkout, product):
    variant = product.variants.get()
    initial_quantity = 1
    replaced_quantity = 4

    add_variant_to_checkout(checkout, variant, initial_quantity)
    data = {"quantity": replaced_quantity}
    form = forms.ReplaceCheckoutLineForm(data=data, checkout=checkout, variant=variant)
    assert form.is_valid()
    form.save()
    assert checkout.quantity == replaced_quantity


def test_replace_checkout_line_form_when_insufficient_stock(
    monkeypatch, checkout, product
):
    variant = product.variants.get()
    initial_quantity = 1
    replaced_quantity = 4

    add_variant_to_checkout(checkout, variant, initial_quantity)
    exception_mock = InsufficientStock(Mock(quantity_available=2))
    monkeypatch.setattr(
        "saleor.product.models.ProductVariant.check_quantity",
        Mock(side_effect=exception_mock),
    )
    data = {"quantity": replaced_quantity}
    form = forms.ReplaceCheckoutLineForm(data=data, checkout=checkout, variant=variant)
    assert not form.is_valid()
    with pytest.raises(KeyError):
        form.save()
    assert checkout.quantity == initial_quantity


def test_find_open_checkout_for_user(customer_user, user_checkout):
    assert find_open_checkout_for_user(customer_user) == user_checkout

    checkout = Checkout.objects.create(user=customer_user)

    assert find_open_checkout_for_user(customer_user) == checkout
    assert not Checkout.objects.filter(pk=user_checkout.pk).exists()


def test_checkout_repr():
    checkout = Checkout()
    assert repr(checkout) == "Checkout(quantity=0)"

    checkout.quantity = 1
    assert repr(checkout) == "Checkout(quantity=1)"


def test_checkout_change_user(customer_user):
    checkout1 = Checkout.objects.create()
    change_checkout_user(checkout1, customer_user)

    checkout2 = Checkout.objects.create()
    change_checkout_user(checkout2, customer_user)

    assert not Checkout.objects.filter(pk=checkout1.pk).exists()


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


def test_get_checkout_context(checkout_with_single_item, shipping_zone, address):
    checkout = checkout_with_single_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    shipment_option = get_shipping_price_estimate(
        checkout, discounts=None, country_code="PL"
    )
    checkout_data = utils.get_checkout_context(
        checkout, None, currency="USD", shipping_range=shipment_option
    )
    assert checkout_data["checkout_total"] == TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    assert checkout_data["total_with_shipping"].start == TaxedMoney(
        net=Money("20.00", "USD"), gross=Money("20.00", "USD")
    )


def test_get_checkout_context_no_shipping(checkout_with_single_item, address):
    checkout = checkout_with_single_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    shipment_option = get_shipping_price_estimate(
        checkout, discounts=None, country_code="PL"
    )
    checkout_data = utils.get_checkout_context(
        checkout, None, currency="USD", shipping_range=shipment_option
    )
    checkout_total = checkout_data["checkout_total"]
    assert checkout_total == TaxedMoney(
        net=Money("10.00", "USD"), gross=Money("10.00", "USD")
    )
    assert checkout_data["total_with_shipping"].start == checkout_total


def test_get_total_weight(checkout_with_item):
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.weight = Weight(kg=10)
    variant.save()
    line.quantity = 6
    line.save()
    assert checkout_with_item.get_total_weight() == Weight(kg=60)
