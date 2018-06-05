import json
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.urls import reverse
from prices import Money, TaxedMoney

from saleor.checkout import forms, utils
from saleor.checkout.context_processors import cart_counter
from saleor.checkout.models import Cart
from saleor.checkout.utils import (
    add_variant_to_cart, change_cart_user, find_open_cart_for_user)
from saleor.checkout.views import update_cart_line
from saleor.core.exceptions import InsufficientStock
from saleor.core.utils.taxes import ZERO_TAXED_MONEY
from saleor.discount.models import Sale
from saleor.shipping.utils import get_shipment_options


@pytest.fixture()
def cart_request_factory(rf, monkeypatch):
    def create_request(user=None, token=None):
        request = rf.get(reverse('home'))
        if user is None:
            request.user = AnonymousUser()
        else:
            request.user = user
        request.discounts = Sale.objects.all()
        request.taxes = None
        monkeypatch.setattr(
            request, 'get_signed_cookie', Mock(return_value=token))
        return request
    return create_request


@pytest.fixture()
def anonymous_cart(db):
    return Cart.objects.get_or_create(user=None)[0]


@pytest.fixture()
def user_cart(customer_user):
    return Cart.objects.get_or_create(user=customer_user)[0]


@pytest.fixture()
def local_currency(monkeypatch):
    def side_effect(price, currency):
        return price
    monkeypatch.setattr('saleor.checkout.views.to_local_currency', side_effect)


def test_get_or_create_anonymous_cart_from_token(anonymous_cart, user_cart):
    queryset = Cart.objects.all()
    carts = list(queryset)
    cart = utils.get_or_create_anonymous_cart_from_token(anonymous_cart.token)
    assert Cart.objects.all().count() == 2
    assert cart == anonymous_cart

    # test against new token
    cart = utils.get_or_create_anonymous_cart_from_token(uuid4())
    assert Cart.objects.all().count() == 3
    assert cart not in carts
    assert cart.user is None
    cart.delete()

    # test against getting cart assigned to user
    cart = utils.get_or_create_anonymous_cart_from_token(user_cart.token)
    assert Cart.objects.all().count() == 3
    assert cart not in carts
    assert cart.user is None


def test_get_or_create_user_cart(
        customer_user, anonymous_cart, user_cart, admin_user):
    cart = utils.get_or_create_user_cart(customer_user)
    assert Cart.objects.all().count() == 2
    assert cart == user_cart

    # test against creating new carts
    Cart.objects.create(user=admin_user)
    queryset = Cart.objects.all()
    carts = list(queryset)
    cart = utils.get_or_create_user_cart(admin_user)
    assert Cart.objects.all().count() == 3
    assert cart in carts
    assert cart.user == admin_user


def test_get_anonymous_cart_from_token(anonymous_cart, user_cart):
    cart = utils.get_anonymous_cart_from_token(anonymous_cart.token)
    assert Cart.objects.all().count() == 2
    assert cart == anonymous_cart

    # test against new token
    cart = utils.get_anonymous_cart_from_token(uuid4())
    assert Cart.objects.all().count() == 2
    assert cart is None

    # test against getting cart assigned to user
    cart = utils.get_anonymous_cart_from_token(user_cart.token)
    assert Cart.objects.all().count() == 2
    assert cart is None


def test_get_user_cart(anonymous_cart, user_cart, admin_user, customer_user):
    cart = utils.get_user_cart(customer_user)
    assert Cart.objects.all().count() == 2
    assert cart == user_cart


def test_get_or_create_cart_from_request(
        cart_request_factory, monkeypatch, customer_user):
    token = uuid4()
    queryset = Cart.objects.all()
    request = cart_request_factory(user=customer_user, token=token)
    user_cart = Cart(user=customer_user)
    anonymous_cart = Cart()
    mock_get_for_user = Mock(return_value=user_cart)
    mock_get_for_anonymous = Mock(return_value=anonymous_cart)
    monkeypatch.setattr(
        'saleor.checkout.utils.get_or_create_user_cart', mock_get_for_user)
    monkeypatch.setattr(
        'saleor.checkout.utils.get_or_create_anonymous_cart_from_token',
        mock_get_for_anonymous)
    returned_cart = utils.get_or_create_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_cart == user_cart

    request = cart_request_factory(user=None, token=token)
    returned_cart = utils.get_or_create_cart_from_request(request, queryset)
    mock_get_for_anonymous.assert_called_once_with(token, queryset)
    assert returned_cart == anonymous_cart


def test_get_cart_from_request(
        monkeypatch, customer_user, cart_request_factory):
    queryset = Cart.objects.all()
    token = uuid4()
    request = cart_request_factory(user=customer_user, token=token)

    user_cart = Cart(user=customer_user)
    mock_get_for_user = Mock(return_value=user_cart)
    monkeypatch.setattr(
        'saleor.checkout.utils.get_user_cart', mock_get_for_user)
    returned_cart = utils.get_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_cart == user_cart

    mock_get_for_user = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.checkout.utils.get_user_cart', mock_get_for_user)
    returned_cart = utils.get_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert not Cart.objects.filter(token=returned_cart.token).exists()

    anonymous_cart = Cart()
    mock_get_for_anonymous = Mock(return_value=anonymous_cart)
    monkeypatch.setattr(
        'saleor.checkout.utils.get_anonymous_cart_from_token',
        mock_get_for_anonymous)
    request = cart_request_factory(user=None, token=token)
    returned_cart = utils.get_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_cart == anonymous_cart

    mock_get_for_anonymous = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.checkout.utils.get_anonymous_cart_from_token',
        mock_get_for_anonymous)
    returned_cart = utils.get_cart_from_request(request, queryset)
    assert not Cart.objects.filter(token=returned_cart.token).exists()


def test_find_and_assign_anonymous_cart(anonymous_cart, customer_user, client):
    cart_token = anonymous_cart.token
    # Anonymous user has a cart with token stored in cookie
    value = signing.get_cookie_signer(salt=utils.COOKIE_NAME).sign(cart_token)
    client.cookies[utils.COOKIE_NAME] = value
    # Anonymous logs in
    response = client.post(
        reverse('account:login'),
        {'username': customer_user.email, 'password': 'password'}, follow=True)
    assert response.context['user'] == customer_user
    # User should have only one cart, the same as he had previously in
    # anonymous session
    authenticated_user_carts = customer_user.carts.all()
    assert authenticated_user_carts.count() == 1
    assert authenticated_user_carts[0].token == cart_token


def test_login_without_a_cart(customer_user, client):
    assert utils.COOKIE_NAME not in client.cookies
    response = client.post(
        reverse('account:login'),
        {'username': customer_user.email, 'password': 'password'}, follow=True)
    assert response.context['user'] == customer_user
    authenticated_user_carts = customer_user.carts.all()
    assert authenticated_user_carts.count() == 0


def test_login_with_incorrect_cookie_token(customer_user, client):
    value = signing.get_cookie_signer(salt=utils.COOKIE_NAME).sign('incorrect')
    client.cookies[utils.COOKIE_NAME] = value
    response = client.post(
        reverse('account:login'),
        {'username': customer_user.email, 'password': 'password'}, follow=True)
    assert response.context['user'] == customer_user
    authenticated_user_carts = customer_user.carts.all()
    assert authenticated_user_carts.count() == 0


def test_find_and_assign_anonymous_cart_and_close_opened(
        customer_user, user_cart, anonymous_cart, cart_request_factory):
    token = anonymous_cart.token
    token_user = user_cart.token
    request = cart_request_factory(user=customer_user, token=token)
    utils.find_and_assign_anonymous_cart()(
        lambda request: Mock(delete_cookie=lambda name: None))(request)
    token_cart = Cart.objects.filter(token=token).first()
    user_cart = Cart.objects.filter(token=token_user).first()
    assert token_cart is not None
    assert token_cart.user.pk == customer_user.pk
    assert not user_cart


def test_adding_without_checking(cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 1000, check_quantity=False)
    assert len(cart) == 1


def test_adding_zero_quantity(cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 0)
    assert len(cart) == 0


def test_adding_same_variant(cart, product, taxes):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 1)
    add_variant_to_cart(cart, variant, 2)
    assert len(cart) == 1
    assert cart.quantity == 3
    cart_total = TaxedMoney(net=Money('24.39', 'USD'), gross=Money(30, 'USD'))
    assert cart.get_subtotal(taxes=taxes) == cart_total


def test_replacing_same_variant(cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 1, replace=True)
    add_variant_to_cart(cart, variant, 2, replace=True)
    assert len(cart) == 1
    assert cart.quantity == 2


def test_adding_invalid_quantity(cart, product):
    variant = product.variants.get()
    with pytest.raises(ValueError):
        add_variant_to_cart(cart, variant, -1)


def test_getting_line(cart, product):
    variant = product.variants.get()
    assert cart.get_line(variant) is None
    add_variant_to_cart(cart, variant)
    assert cart.lines.get() == cart.get_line(variant)


def test_shipping_detection(cart, product):
    assert not cart.is_shipping_required()
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, replace=True)
    assert cart.is_shipping_required()


def test_cart_counter(monkeypatch):
    monkeypatch.setattr(
        'saleor.checkout.context_processors.get_cart_from_request',
        Mock(return_value=Mock(quantity=4)))
    ret = cart_counter(Mock())
    assert ret == {'cart_counter': 4}


def test_get_product_variants_and_prices():
    variant = Mock(product_id=1, id=1, get_price=Mock(return_value=10))
    cart = MagicMock(spec=Cart)
    cart.__iter__ = Mock(
        return_value=iter([Mock(quantity=1, variant=variant)]))
    variants = list(utils.get_product_variants_and_prices(cart, variant))
    assert variants == [(variant, 10)]


def test_contains_unavailable_variants():
    missing_variant = Mock(
        check_quantity=Mock(side_effect=InsufficientStock('')))
    cart = MagicMock()
    cart.__iter__ = Mock(return_value=iter([Mock(variant=missing_variant)]))
    assert utils.contains_unavailable_variants(cart)

    variant = Mock(check_quantity=Mock())
    cart.__iter__ = Mock(return_value=iter([Mock(variant=variant)]))
    assert not utils.contains_unavailable_variants(cart)


def test_remove_unavailable_variants(cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant)
    variant.quantity = 0
    variant.save()
    utils.remove_unavailable_variants(cart)
    assert len(cart) == 0


def test_check_product_availability_and_warn(
        monkeypatch, cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant)
    monkeypatch.setattr(
        'django.contrib.messages.warning', Mock(warning=Mock()))
    monkeypatch.setattr(
        'saleor.checkout.utils.contains_unavailable_variants',
        Mock(return_value=False))

    utils.check_product_availability_and_warn(MagicMock(), cart)
    assert len(cart) == 1

    monkeypatch.setattr(
        'saleor.checkout.utils.contains_unavailable_variants',
        Mock(return_value=True))
    monkeypatch.setattr(
        'saleor.checkout.utils.remove_unavailable_variants',
        lambda c: add_variant_to_cart(cart, variant, 0, replace=True))

    utils.check_product_availability_and_warn(MagicMock(), cart)
    assert len(cart) == 0


def test_add_to_cart_form(cart, product):
    variant = product.variants.get()
    add_variant_to_cart(cart, variant, 3)
    data = {'quantity': 1}
    form = forms.AddToCartForm(data=data, cart=cart, product=product)

    form.get_variant = Mock(return_value=variant)

    assert form.is_valid()
    form.save()
    assert cart.lines.count() == 1
    assert cart.lines.filter(variant=variant).exists()

    with pytest.raises(NotImplementedError):
        data = {'quantity': 1}
        form = forms.AddToCartForm(data=data, cart=cart, product=product)
        form.is_valid()
    data = {}

    form = forms.AddToCartForm(data=data, cart=cart, product=product)
    assert not form.is_valid()


def test_form_when_variant_does_not_exist():
    cart_lines = []
    cart = Mock(
        add=lambda variant, quantity: cart_lines.append(Mock()),
        get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    form.get_variant = Mock(side_effect=ObjectDoesNotExist)
    assert not form.is_valid()


@pytest.mark.parametrize('track_inventory', (True, False))
def test_add_to_cart_form_when_insufficient_stock(product, track_inventory):
    variant = product.variants.first()
    variant.track_inventory = track_inventory
    variant.save()

    cart_lines = []
    cart = Mock(
        add=lambda variant, quantity: cart_lines.append(variant),
        get_line=Mock(return_value=Mock(quantity=49)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    form.get_variant = Mock(return_value=variant)

    if track_inventory:
        assert not form.is_valid()
    else:
        assert form.is_valid()


def test_replace_cart_line_form(cart, product):
    variant = product.variants.get()
    initial_quantity = 1
    replaced_quantity = 4

    add_variant_to_cart(cart, variant, initial_quantity)
    data = {'quantity': replaced_quantity}
    form = forms.ReplaceCartLineForm(data=data, cart=cart, variant=variant)
    assert form.is_valid()
    form.save()
    assert cart.quantity == replaced_quantity


def test_replace_cartline_form_when_insufficient_stock(
        monkeypatch, cart, product):
    variant = product.variants.get()
    initial_quantity = 1
    replaced_quantity = 4

    add_variant_to_cart(cart, variant, initial_quantity)
    exception_mock = InsufficientStock(
        Mock(quantity_available=2))
    monkeypatch.setattr(
        'saleor.product.models.ProductVariant.check_quantity',
        Mock(side_effect=exception_mock))
    data = {'quantity': replaced_quantity}
    form = forms.ReplaceCartLineForm(data=data, cart=cart, variant=variant)
    assert not form.is_valid()
    with pytest.raises(KeyError):
        form.save()
    assert cart.quantity == initial_quantity


def test_view_empty_cart(client, request_cart):
    response = client.get(reverse('cart:index'))
    assert response.status_code == 200


def test_view_cart_without_taxes(client, sale, request_cart_with_item):
    response = client.get(reverse('cart:index'))
    response_cart_line = response.context[0]['cart_lines'][0]
    cart_line = request_cart_with_item.lines.first()
    assert not response_cart_line['get_total'].tax.amount
    assert not response_cart_line['get_total'] == cart_line.get_total()
    assert response.status_code == 200


def test_view_cart_with_taxes(
        settings, client, sale, request_cart_with_item, vatlayer):
    settings.DEFAULT_COUNTRY = 'PL'
    response = client.get(reverse('cart:index'))
    response_cart_line = response.context[0]['cart_lines'][0]
    cart_line = request_cart_with_item.lines.first()
    assert response_cart_line['get_total'].tax.amount
    assert not response_cart_line['get_total'] == cart_line.get_total(
        taxes=vatlayer)
    assert response.status_code == 200


def test_view_update_cart_quantity(
        client, local_currency, request_cart_with_item):
    variant = request_cart_with_item.lines.get().variant
    response = client.post(
        reverse('cart:update-line', kwargs={'variant_id': variant.pk}),
        data={'quantity': 3}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    assert request_cart_with_item.quantity == 3


def test_view_update_cart_quantity_with_taxes(
        client, local_currency, request_cart_with_item, vatlayer):
    variant = request_cart_with_item.lines.get().variant
    response = client.post(
        reverse('cart:update-line', kwargs={'variant_id': variant.id}),
        {'quantity': 3}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    assert request_cart_with_item.quantity == 3


def test_view_invalid_update_cart(client, request_cart_with_item):
    variant = request_cart_with_item.lines.get().variant
    response = client.post(
        reverse('cart:update-line', kwargs={'variant_id': variant.pk}),
        data={}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 400
    assert 'error' in resp_decoded.keys()
    assert request_cart_with_item.quantity == 1


def test_cart_page_without_openexchagerates(
        client, request_cart_with_item, settings):
    settings.OPENEXCHANGERATES_API_KEY = None
    response = client.get(reverse('cart:index'))
    context = response.context
    assert context['local_cart_total'] is None


def test_cart_page_with_openexchagerates(
        client, monkeypatch, request_cart_with_item, settings):
    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'
    response = client.get(reverse('cart:index'))
    context = response.context
    assert context['local_cart_total'] is None
    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})
    response = client.get(reverse('cart:index'))
    context = response.context
    assert context['local_cart_total'].currency == 'PLN'


def test_cart_summary_page(settings, client, request_cart_with_item, vatlayer):
    settings.DEFAULT_COUNTRY = 'PL'
    response = client.get(reverse('cart:summary'))
    assert response.status_code == 200
    content = response.context
    assert content['quantity'] == request_cart_with_item.quantity
    cart_total = request_cart_with_item.get_subtotal(taxes=vatlayer)
    assert content['total'] == cart_total
    assert len(content['lines']) == 1
    cart_line = content['lines'][0]
    variant = request_cart_with_item.lines.get().variant
    assert cart_line['variant'] == variant.name
    assert cart_line['quantity'] == 1


def test_cart_summary_page_empty_cart(client, request_cart):
    response = client.get(reverse('cart:summary'))
    assert response.status_code == 200
    data = response.context
    assert data['quantity'] == 0


def test_cart_line_total_with_discount_and_taxes(
        sale, request_cart_with_item, taxes):
    sales = Sale.objects.all()
    line = request_cart_with_item.lines.first()
    assert line.get_total(discounts=sales, taxes=taxes) == TaxedMoney(
        net=Money('4.07', 'USD'), gross=Money('5.00', 'USD'))


def test_find_open_cart_for_user(customer_user, user_cart):
    assert find_open_cart_for_user(customer_user) == user_cart

    cart = Cart.objects.create(user=customer_user)

    assert find_open_cart_for_user(customer_user) == cart
    assert not Cart.objects.filter(pk=user_cart.pk).exists()


def test_cart_repr():
    cart = Cart()
    assert repr(cart) == 'Cart(quantity=0)'

    cart.quantity = 1
    assert repr(cart) == 'Cart(quantity=1)'


def test_cart_get_total_empty(db):
    cart = Cart.objects.create()
    assert cart.get_subtotal() == ZERO_TAXED_MONEY


def test_cart_change_user(customer_user):
    cart1 = Cart.objects.create()
    change_cart_user(cart1, customer_user)

    cart2 = Cart.objects.create()
    change_cart_user(cart2, customer_user)

    assert not Cart.objects.filter(pk=cart1.pk).exists()


def test_cart_line_repr(product, request_cart_with_item):
    variant = product.variants.get()
    line = request_cart_with_item.lines.first()
    assert repr(line) == 'CartLine(variant=%r, quantity=%r)' % (
        variant, line.quantity)


def test_cart_line_state(product, request_cart_with_item):
    variant = product.variants.get()
    line = request_cart_with_item.lines.first()

    assert line.__getstate__() == (variant, line.quantity)

    line.__setstate__((variant, 2))

    assert line.quantity == 2


def test_get_category_variants_and_prices(
        default_category, product, request_cart_with_item):
    result = list(utils.get_category_variants_and_prices(
        request_cart_with_item, default_category))
    variant = product.variants.get()
    assert result[0][0] == variant


def test_update_view_must_be_ajax(customer_user, rf):
    request = rf.post(reverse('home'))
    request.user = customer_user
    request.discounts = None
    result = update_cart_line(request, 1)
    assert result.status_code == 302


def test_get_or_create_db_cart(customer_user, db, rf):
    def view(request, cart, *args, **kwargs):
        return HttpResponse()

    decorated_view = utils.get_or_create_db_cart()(view)
    assert Cart.objects.filter(user=customer_user).count() == 0
    request = rf.get(reverse('home'))
    request.user = customer_user
    decorated_view(request)
    assert Cart.objects.filter(user=customer_user).count() == 1

    request.user = AnonymousUser()
    decorated_view(request)
    assert Cart.objects.filter(user__isnull=True).count() == 1


def test_get_cart_data(request_cart_with_item, shipping_method, vatlayer):
    shipment_option = get_shipment_options('PL', vatlayer)
    cart_data = utils.get_cart_data(
        request_cart_with_item, shipment_option, 'USD', None, vatlayer)
    assert cart_data['cart_total'] == TaxedMoney(
        net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    assert cart_data['total_with_shipping'].start == TaxedMoney(
        net=Money('16.26', 'USD'), gross=Money(20, 'USD'))


def test_get_cart_data_no_shipping(request_cart_with_item, vatlayer):
    shipment_option = get_shipment_options('PL', vatlayer)
    cart_data = utils.get_cart_data(
        request_cart_with_item, shipment_option, 'USD', None, vatlayer)
    cart_total = cart_data['cart_total']
    assert cart_total == TaxedMoney(
        net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    assert cart_data['total_with_shipping'].start == cart_total


def test_cart_total_with_discount(request_cart_with_item, sale, vatlayer):
    total = (
        request_cart_with_item.get_total(discounts=(sale,), taxes=vatlayer))
    assert total == TaxedMoney(
        net=Money('4.07', 'USD'), gross=Money('5.00', 'USD'))


def test_cart_taxes(request_cart_with_item, shipping_method, vatlayer):
    cart = request_cart_with_item
    cart.shipping_method = shipping_method.price_per_country.get()
    cart.save()
    taxed_price = TaxedMoney(net=Money('8.13', 'USD'), gross=Money(10, 'USD'))
    assert cart.get_shipping_price(taxes=vatlayer) == taxed_price
    assert cart.get_subtotal(taxes=vatlayer) == taxed_price
