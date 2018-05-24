import datetime
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django_countries.fields import Country
from freezegun import freeze_time
from prices import Money, TaxedMoney

from saleor.account.models import Address
from saleor.cart.checkout import views
from saleor.cart.checkout.forms import CartVoucherForm
from saleor.cart.checkout.utils import (
    create_order, get_checkout_data, get_taxes_for_cart,
    get_voucher_discount_for_cart, get_voucher_for_cart,
    recalculate_cart_discount, remove_voucher_from_cart,
    save_billing_address_in_cart, save_shipping_address_in_cart)
from saleor.cart.utils import add_variant_to_cart
from saleor.core.exceptions import InsufficientStock
from saleor.core.utils.taxes import (
    ZERO_MONEY, ZERO_TAXED_MONEY, get_taxes_for_country)
from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.models import NotApplicable, Voucher

from .utils import compare_taxes


@pytest.mark.parametrize('cart, status_code, url', [
    (Mock(__len__=Mock(return_value=0)), 302, reverse('cart:index')),
    (
        Mock(
            __len__=Mock(return_value=1),
            is_shipping_required=Mock(return_value=True)),
        302, reverse('cart:checkout-shipping-address')),
    (
        Mock(
            __len__=Mock(return_value=1),
            is_shipping_required=Mock(return_value=False)),
        302, reverse('cart:checkout-summary')),
    (
        Mock(
            __len__=Mock(return_value=0),
            is_shipping_required=Mock(return_value=False)),
        302, reverse('cart:index'))])
def test_index_view(cart, status_code, url, rf, monkeypatch):
    monkeypatch.setattr(
        'saleor.cart.utils.get_cart_from_request', lambda req, qs: cart)
    request = rf.get('cart:checkout-index', follow=True)

    response = views.index_view(request)

    assert response.status_code == status_code
    assert response.url == url


def test_checkout_discount(request_cart_with_item, sale, vatlayer):
    total = (
        request_cart_with_item.get_total(discounts=(sale,), taxes=vatlayer))
    assert total == TaxedMoney(
        net=Money('4.07', 'USD'), gross=Money('5.00', 'USD'))


def test_checkout_create_order_insufficient_stock(
        request_cart, customer_user, product_without_shipping):
    variant = product_without_shipping.variants.get()
    add_variant_to_cart(request_cart, variant, 10, check_quantity=False)
    request_cart.user = customer_user
    request_cart.billing_address = customer_user.default_billing_address
    request_cart.save()

    with pytest.raises(InsufficientStock):
        create_order(
            request_cart, 'tracking_code', discounts=None, taxes=None)


def test_checkout_taxes(request_cart_with_item, shipping_method, vatlayer):
    cart = request_cart_with_item
    cart.shipping_method = shipping_method.price_per_country.get()
    cart.save()
    taxed_price = TaxedMoney(net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    assert cart.get_shipping_price(taxes=vatlayer) == taxed_price
    assert cart.get_subtotal(taxes=vatlayer) == taxed_price


def test_note_in_created_order(request_cart_with_item, address):
    request_cart_with_item.shipping_address = address
    request_cart_with_item.note = ''
    request_cart_with_item.save()
    order = create_order(
        request_cart_with_item, 'tracking_code', discounts=None, taxes=None)
    assert not order.notes.all()

    request_cart_with_item.note = 'test_note'
    request_cart_with_item.save()
    order = create_order(
        request_cart_with_item, 'tracking_code', discounts=None, taxes=None)
    assert order.notes.filter(content='test_note').exists()


@pytest.mark.parametrize(
    'total, discount_value, discount_type, limit, expected_value', [
        ('100', 10, DiscountValueType.FIXED, None, 10),
        ('100.05', 10, DiscountValueType.PERCENTAGE, 100, 10)])
def test_value_voucher_checkout_discount(
        settings, total, discount_value, discount_type, limit, expected_value):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Money(limit, 'USD') if limit is not None else None)
    subtotal = TaxedMoney(net=Money(total, 'USD'), gross=Money(total, 'USD'))
    cart = Mock(get_subtotal=Mock(return_value=subtotal))
    discount = get_voucher_discount_for_cart(voucher, cart)
    assert discount == Money(expected_value, 'USD')


def test_value_voucher_checkout_discount_not_applicable(settings):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        limit=Money(100, 'USD'))
    subtotal = TaxedMoney(net=Money(10, 'USD'), gross=Money(10, 'USD'))
    cart = Mock(get_subtotal=Mock(return_value=subtotal))
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_cart(voucher, cart)
    assert e.value.limit == Money(100, 'USD')


@pytest.mark.parametrize(
    'shipping_cost, shipping_country_code, discount_value, discount_type, apply_to, expected_value', [  # noqa
        (10, None, 50, DiscountValueType.PERCENTAGE, None, 5),
        (10, None, 20, DiscountValueType.FIXED, None, 10),
        (10, 'PL', 20, DiscountValueType.FIXED, '', 10),
        (5, 'PL', 5, DiscountValueType.FIXED, 'PL', 5)])
def test_shipping_voucher_checkout_discount(
        settings, shipping_cost, shipping_country_code, discount_value,
        discount_type, apply_to, expected_value):
    subtotal = TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD'))
    shipping_total = TaxedMoney(
        net=Money(shipping_cost, 'USD'), gross=Money(shipping_cost, 'USD'))
    cart = Mock(
        get_subtotal=Mock(return_value=subtotal),
        is_shipping_required=Mock(return_value=True),
        shipping_method=Mock(
            price=Money(shipping_cost, 'USD'),
            country_code=shipping_country_code,
            get_total_price=Mock(return_value=shipping_total)))
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_to=apply_to,
        limit=None)
    discount = get_voucher_discount_for_cart(voucher, cart)
    assert discount == Money(expected_value, 'USD')


@pytest.mark.parametrize(
    'is_shipping_required, shipping_method, discount_value, discount_type, '
    'apply_to, limit, subtotal, error_msg', [
        (True, Mock(country_code='PL'), 10, DiscountValueType.FIXED,
         'US', None, Money(10, 'USD'),
         'This offer is only valid in United States of America.'),
        (True, None, 10, DiscountValueType.FIXED,
         None, None, Money(10, 'USD'),
         'Please select a shipping method first.'),
        (False, None, 10, DiscountValueType.FIXED,
         None, None, Money(10, 'USD'),
         'Your order does not require shipping.'),
        (True, Mock(price=Money(10, 'USD')), 10,
         DiscountValueType.FIXED, None, 5, Money(2, 'USD'),
         'This offer is only valid for orders over $5.00.')])
def test_shipping_voucher_checkout_discount_not_applicable(
        settings, is_shipping_required, shipping_method, discount_value,
        discount_type, apply_to, limit, subtotal, error_msg):
    subtotal_price = TaxedMoney(net=subtotal, gross=subtotal)
    cart = Mock(
        get_subtotal=Mock(return_value=subtotal_price),
        is_shipping_required=Mock(return_value=is_shipping_required),
        shipping_method=shipping_method)
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        limit=Money(limit, 'USD') if limit is not None else None,
        apply_to=apply_to)
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_cart(voucher, cart)
    assert str(e.value) == error_msg


def test_product_voucher_checkout_discount_not_applicable(
        settings, monkeypatch):
    monkeypatch.setattr(
        'saleor.cart.checkout.utils.get_product_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    cart=Mock()

    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_cart(voucher, cart)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_category_voucher_checkout_discount_not_applicable(
        settings, monkeypatch):
    monkeypatch.setattr(
        'saleor.cart.checkout.utils.get_category_variants_and_prices',
        lambda cart, product: [])
    voucher = Voucher(
        code='unique', type=VoucherType.CATEGORY,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    cart = Mock()
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_cart(voucher, cart)
    assert str(e.value) == 'This offer is only valid for selected items.'


def test_checkout_discount_form_invalid_voucher_code(
        monkeypatch, request_cart_with_item):
    form = CartVoucherForm(
        {'voucher': 'invalid'}, instance=request_cart_with_item)
    assert not form.is_valid()
    assert 'voucher' in form.errors


def test_checkout_discount_form_not_applicable_voucher(
        voucher, request_cart_with_item):
    voucher.limit = 200
    voucher.save()
    form = CartVoucherForm(
        {'voucher': voucher.code}, instance=request_cart_with_item)
    assert not form.is_valid()
    assert 'voucher' in form.errors


def test_checkout_discount_form_active_queryset_voucher_not_active(
        voucher, request_cart_with_item):
    assert Voucher.objects.count() == 1
    voucher.start_date = datetime.date.today() + datetime.timedelta(days=1)
    voucher.save()
    form = CartVoucherForm(
        {'voucher': voucher.code}, instance=request_cart_with_item)
    qs = form.fields['voucher'].queryset
    assert qs.count() == 0


def test_checkout_discount_form_active_queryset_voucher_active(
        voucher, request_cart_with_item):
    assert Voucher.objects.count() == 1
    voucher.start_date = datetime.date.today()
    voucher.save()
    form = CartVoucherForm(
        {'voucher': voucher.code}, instance=request_cart_with_item)
    qs = form.fields['voucher'].queryset
    assert qs.count() == 1


def test_checkout_discount_form_active_queryset_after_some_time(
        voucher, request_cart_with_item):
    assert Voucher.objects.count() == 1
    voucher.start_date = datetime.date(year=2016, month=6, day=1)
    voucher.end_date = datetime.date(year=2016, month=6, day=2)
    voucher.save()

    with freeze_time('2016-05-31'):
        form = CartVoucherForm(
            {'voucher': voucher.code}, instance=request_cart_with_item)
        assert form.fields['voucher'].queryset.count() == 0

    with freeze_time('2016-06-01'):
        form = CartVoucherForm(
            {'voucher': voucher.code}, instance=request_cart_with_item)
        assert form.fields['voucher'].queryset.count() == 1

    with freeze_time('2016-06-03'):
        form = CartVoucherForm(
            {'voucher': voucher.code}, instance=request_cart_with_item)
        assert form.fields['voucher'].queryset.count() == 0


def test_get_taxes_for_cart(cart, vatlayer):
    taxes = get_taxes_for_cart(cart, vatlayer)
    compare_taxes(taxes, vatlayer)


def test_get_taxes_for_cart_with_shipping_address(cart, address, vatlayer):
    address.country = 'DE'
    address.save()
    cart.shipping_address = address
    cart.save()
    taxes = get_taxes_for_cart(cart, vatlayer)
    compare_taxes(taxes, get_taxes_for_country(Country('DE')))


def test_get_voucher_for_cart(cart_with_voucher, voucher):
    cart_voucher = get_voucher_for_cart(cart_with_voucher)
    assert cart_voucher == voucher


def test_get_voucher_for_cart_expired_voucher(cart_with_voucher, voucher):
    date_yesterday = datetime.date.today() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()
    cart_voucher = get_voucher_for_cart(cart_with_voucher)
    assert cart_voucher is None


def test_get_voucher_for_cart_no_voucher_code(cart):
    cart_voucher = get_voucher_for_cart(cart)
    assert cart_voucher is None


def test_remove_voucher_from_cart(cart_with_voucher):
    cart = cart_with_voucher
    remove_voucher_from_cart(cart)

    assert not cart.voucher_code
    assert not cart.discount_name
    assert cart.discount_amount == ZERO_MONEY


def test_recalculate_cart_discount(cart_with_voucher, voucher):
    voucher.discount_value = 10
    voucher.save()

    recalculate_cart_discount(cart_with_voucher)

    assert cart_with_voucher.discount_amount == Money('10.00', 'USD')


def test_recalculate_cart_discount_voucher_not_applicable(
        cart_with_voucher, voucher):
    cart = cart_with_voucher
    voucher.limit = 100
    voucher.save()

    recalculate_cart_discount(cart_with_voucher)

    assert not cart.voucher_code
    assert not cart.discount_name
    assert cart.discount_amount == ZERO_MONEY


def test_recalculate_cart_discount_expired_voucher(cart_with_voucher, voucher):
    cart = cart_with_voucher
    date_yesterday = datetime.date.today() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()

    recalculate_cart_discount(cart_with_voucher)

    assert not cart.voucher_code
    assert not cart.discount_name
    assert cart.discount_amount == ZERO_MONEY


def test_get_checkout_data(cart_with_voucher, vatlayer):
    line_price = TaxedMoney(net=Money('24.39', 'USD'), gross=Money('30.00', 'USD'))
    expected_data = {
        'cart': cart_with_voucher,
        'cart_are_taxes_handled': True,
        'cart_lines': [(cart_with_voucher.lines.first(), line_price)],
        'cart_shipping_price': ZERO_TAXED_MONEY,
        'cart_subtotal': line_price,
        'cart_total': line_price - cart_with_voucher.discount_amount}

    data = get_checkout_data(cart_with_voucher, discounts=None, taxes=vatlayer)

    assert data == expected_data


def test_save_address_in_cart(cart, address):
    save_shipping_address_in_cart(cart, address)
    save_billing_address_in_cart(cart, address)

    cart.refresh_from_db()
    assert cart.shipping_address == address
    assert cart.billing_address == address


def test_save_address_in_cart_to_none(cart, address):
    cart.shipping_address = address
    cart.billing_address = address.get_copy()
    cart.save()

    save_shipping_address_in_cart(cart, None)
    save_billing_address_in_cart(cart, None)

    cart.refresh_from_db()
    assert cart.shipping_address is None
    assert cart.billing_address is None


def test_save_address_in_cart_to_same(cart, address):
    cart.shipping_address = address
    cart.billing_address = address.get_copy()
    cart.save(update_fields=['shipping_address', 'billing_address'])
    shipping_address_id = cart.shipping_address.id
    billing_address_id = cart.billing_address.id

    save_shipping_address_in_cart(cart, address)
    save_billing_address_in_cart(cart, address)

    cart.refresh_from_db()
    assert cart.shipping_address.id == shipping_address_id
    assert cart.billing_address.id == billing_address_id


def test_save_address_in_cart_to_other(cart, address):
    address_id = address.id
    cart.shipping_address = address
    cart.billing_address = address.get_copy()
    cart.save(update_fields=['shipping_address', 'billing_address'])
    other_address = Address.objects.create(country=Country('DE'))

    save_shipping_address_in_cart(cart, other_address)
    save_billing_address_in_cart(cart, other_address)

    cart.refresh_from_db()
    assert cart.shipping_address == other_address
    assert cart.billing_address == other_address
    assert not Address.objects.filter(id=address_id).exists()


def test_save_address_in_cart_to_other_with_user(cart, customer_user, address):
    address_id = address.id
    cart.user = customer_user
    cart.shipping_address = address
    cart.billing_address = address.get_copy()
    cart.save(update_fields=['shipping_address', 'billing_address'])
    other_address = Address.objects.create(country=Country('DE'))

    save_shipping_address_in_cart(cart, other_address)
    save_billing_address_in_cart(cart, other_address)

    cart.refresh_from_db()
    assert cart.shipping_address == other_address
    assert cart.billing_address == other_address
    assert Address.objects.filter(id=address_id).exists()
