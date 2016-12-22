from __future__ import unicode_literals

import json
from uuid import uuid4

import pytest
from babeldjango.templatetags.babel import currencyfmt
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from mock import MagicMock, Mock
from satchless.item import InsufficientStock

from saleor.cart import forms, utils
from saleor.cart.models import Cart


@pytest.fixture()
def cart_request_factory(rf, monkeypatch):
    def create_request(user=None, token=None):
        request = rf.get('/')
        if user is None:
            request.user = AnonymousUser()
        else:
            request.user = user
        monkeypatch.setattr(request, 'get_signed_cookie',
                            Mock(return_value=token))
        return request
    return create_request


@pytest.fixture()
def opened_anonymous_cart(customer_user):
    return Cart.objects.get_or_create(user=None, status=Cart.OPEN)[0]


@pytest.fixture()
def cancelled_anonymous_cart(customer_user):
    return Cart.objects.get_or_create(user=None, status=Cart.CANCELED)[0]


@pytest.fixture()
def opened_user_cart(customer_user):
    return Cart.objects.get_or_create(user=customer_user, status=Cart.OPEN)[0]


@pytest.fixture()
def cancelled_user_cart(customer_user):
    return Cart.objects.get_or_create(user=customer_user,
                                      status=Cart.CANCELED)[0]


def test_get_or_create_anonymous_cart_from_token(opened_anonymous_cart,
                                                 cancelled_anonymous_cart,
                                                 opened_user_cart,
                                                 cancelled_user_cart):
    queryset = Cart.objects.all()
    carts = list(queryset)
    cart = utils.get_or_create_anonymous_cart_from_token(opened_anonymous_cart.token)
    assert Cart.objects.all().count() == 4
    assert cart == opened_anonymous_cart

    # test against getting closed carts
    cart = utils.get_or_create_anonymous_cart_from_token(
        cancelled_anonymous_cart.token)
    assert Cart.objects.all().count() == 5
    assert cart not in carts
    assert cart.user is None
    assert cart.status == Cart.OPEN
    cart.delete()

    # test against new token
    cart = utils.get_or_create_anonymous_cart_from_token(uuid4())
    assert Cart.objects.all().count() == 5
    assert cart not in carts
    assert cart.user is None
    assert cart.status == Cart.OPEN
    cart.delete()

    # test against getting cart assigned to user
    cart = utils.get_or_create_anonymous_cart_from_token(opened_user_cart.token)
    assert Cart.objects.all().count() == 5
    assert cart not in carts
    assert cart.user is None
    assert cart.status == Cart.OPEN
    cart.delete()


def test_get_or_create_user_cart(customer_user, opened_anonymous_cart,
                                 cancelled_anonymous_cart, opened_user_cart,
                                 cancelled_user_cart, admin_user):
    cart = utils.get_or_create_user_cart(customer_user)
    assert Cart.objects.all().count() == 4
    assert cart == opened_user_cart

    # test against getting closed carts
    Cart.objects.create(user=admin_user, status=Cart.CANCELED)
    queryset = Cart.objects.all()
    carts = list(queryset)
    cart = utils.get_or_create_user_cart(admin_user)
    assert Cart.objects.all().count() == 6
    assert cart not in carts
    assert cart.user is admin_user
    assert cart.status == Cart.OPEN
    cart.delete()


def test_get_anonymous_cart_from_token(opened_anonymous_cart,
                                       cancelled_anonymous_cart,
                                       opened_user_cart,
                                       cancelled_user_cart):
    cart = utils.get_anonymous_cart_from_token(opened_anonymous_cart.token)
    assert Cart.objects.all().count() == 4
    assert cart == opened_anonymous_cart

    # test against getting closed carts
    cart = utils.get_anonymous_cart_from_token(cancelled_anonymous_cart.token)
    assert Cart.objects.all().count() == 4
    assert cart is None

    # test against new token
    cart = utils.get_anonymous_cart_from_token(uuid4())
    assert Cart.objects.all().count() == 4
    assert cart is None

    # test against getting cart assigned to user
    cart = utils.get_anonymous_cart_from_token(opened_user_cart.token)
    assert Cart.objects.all().count() == 4
    assert cart is None


def test_get_user_cart(opened_anonymous_cart, cancelled_anonymous_cart,
                       opened_user_cart, cancelled_user_cart, admin_user,
                       customer_user):
    cart = utils.get_user_cart(customer_user)
    assert Cart.objects.all().count() == 4
    assert cart == opened_user_cart

    # test against getting closed carts
    Cart.objects.create(user=admin_user, status=Cart.CANCELED)
    queryset = Cart.objects.all()
    carts = list(queryset)
    cart = utils.get_user_cart(admin_user)
    assert Cart.objects.all().count() == 5
    assert cart is None


def test_get_or_create_cart_from_request(cart_request_factory, monkeypatch,
                                         customer_user):
    token = uuid4()
    queryset = Cart.objects.all()
    request = cart_request_factory(user=customer_user, token=token)
    user_cart = Cart(user=customer_user)
    anonymous_cart = Cart()
    mock_get_for_user = Mock(return_value=user_cart)
    mock_get_for_anonymous = Mock(return_value=anonymous_cart)
    monkeypatch.setattr('saleor.cart.utils.get_or_create_user_cart',
                        mock_get_for_user)
    monkeypatch.setattr(
        'saleor.cart.utils.get_or_create_anonymous_cart_from_token',
        mock_get_for_anonymous)
    returned_cart = utils.get_or_create_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_cart == user_cart

    request = cart_request_factory(user=None, token=token)
    returned_cart = utils.get_or_create_cart_from_request(request, queryset)
    mock_get_for_anonymous.assert_called_once_with(token, queryset)
    assert returned_cart == anonymous_cart


def test_get_cart_from_request(monkeypatch, customer_user,
                               cart_request_factory):
    queryset = Cart.objects.all()
    token = uuid4()
    request = cart_request_factory(user=customer_user, token=token)
    user_cart = Cart(user=customer_user)
    mock_get_for_user = Mock(return_value=user_cart)
    monkeypatch.setattr('saleor.cart.utils.get_user_cart',
                        mock_get_for_user)
    returned_cart = utils.get_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_cart == user_cart

    mock_get_for_user = Mock(return_value=None)
    monkeypatch.setattr('saleor.cart.utils.get_user_cart',
                        mock_get_for_user)
    returned_cart = utils.get_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert not Cart.objects.filter(token=returned_cart.token).exists()

    anonymous_cart = Cart()
    mock_get_for_anonymous = Mock(return_value=anonymous_cart)
    monkeypatch.setattr(
        'saleor.cart.utils.get_anonymous_cart_from_token',
        mock_get_for_anonymous)
    request = cart_request_factory(user=None, token=token)
    returned_cart = utils.get_cart_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_cart == anonymous_cart

    mock_get_for_anonymous = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.cart.utils.get_anonymous_cart_from_token',
        mock_get_for_anonymous)
    returned_cart = utils.get_cart_from_request(request, queryset)
    assert not Cart.objects.filter(token=returned_cart.token).exists()


def test_find_and_assign_anonymous_cart(opened_anonymous_cart,
                                        cancelled_anonymous_cart,
                                        opened_user_cart, cancelled_user_cart,
                                        customer_user, cart_request_factory):
    request = cart_request_factory(user=customer_user, token=None)
    anonymous_carts = Cart.objects.filter(user=None).count()
    utils.find_and_assign_anonymous_cart(request)
    assert Cart.objects.filter(user=None).count() == anonymous_carts


def test_find_and_assign_anonymous_cart_and_close_opened(customer_user,
                                                         opened_user_cart,
                                                         opened_anonymous_cart,
                                                         cart_request_factory):
    token = opened_anonymous_cart.token
    token_user = opened_user_cart.token
    request = cart_request_factory(user=customer_user, token=token)
    utils.find_and_assign_anonymous_cart(request)
    token_cart = Cart.objects.filter(token=token).first()
    user_cart = Cart.objects.filter(token=token_user).first()
    assert token_cart.user.pk == customer_user.pk
    assert token_cart.status == Cart.OPEN
    assert user_cart.status == Cart.CANCELED


def test_adding_without_checking(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    cart.add(variant, 1000, check_quantity=False)
    assert len(cart) == 1


def test_adding_zero_quantity(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    cart.add(variant, 0)
    assert len(cart) == 0


def test_adding_same_variant(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    cart.add(variant, 1)
    cart.add(variant, 2)
    price_total = 10 * 3
    assert len(cart) == 1
    assert cart.count() == {'total_quantity': 3}
    assert cart.get_total().gross == price_total


def test_replacing_same_variant(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    cart.add(variant, 1, replace=True)
    cart.add(variant, 2, replace=True)
    assert len(cart) == 1
    assert cart.count() == {'total_quantity': 2}


def test_adding_invalid_quantity(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    with pytest.raises(ValueError):
        cart.add(variant, -1)


@pytest.mark.parametrize('create_line_data, get_line_data, lines_equal', [
    (None, None, True),
    ({'gift-wrap': True}, None, False),
    ({'gift-wrap': True}, {'gift-wrap': True}, True)
])
def test_getting_line(create_line_data, get_line_data, lines_equal,
                      cart, product_in_stock):
    variant = product_in_stock.variants.get()
    assert cart.get_line(variant) is None
    line = cart.create_line(variant, 1, create_line_data)
    fetched_line = cart.get_line(variant, data=get_line_data)
    lines_are_equal = fetched_line == line
    assert lines_equal is lines_are_equal


def test_change_status(cart):
    with pytest.raises(ValueError):
        cart.change_status('spanish inquisition')

    cart.change_status(Cart.OPEN)
    assert cart.status == Cart.OPEN
    cart.change_status(Cart.CANCELED)
    assert cart.status == Cart.CANCELED


def test_shipping_detection(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    assert not cart.is_shipping_required()
    cart.add(variant, 1, replace=True)
    assert cart.is_shipping_required()


def test_get_product_variants_and_prices():
    variant = Mock(product_id=1, id=1)
    cart = MagicMock(spec=Cart)
    cart.lines.all.return_value = [
        Mock(quantity=1, variant=variant,
             get_price_per_item=Mock(return_value=10))]
    variants = list(utils.get_product_variants_and_prices(cart, variant))
    assert variants == [(variant, 10)]


def test_contains_unavailable_variants():
    missing_variant = Mock(
        check_quantity=Mock(side_effect=InsufficientStock('')))
    cart = MagicMock()
    cart.lines.all.return_value = [Mock(variant=missing_variant)]
    assert utils.contains_unavailable_variants(cart)

    variant = Mock(check_quantity=Mock())
    cart.lines.all.return_value = [Mock(variant=variant)]
    assert not utils.contains_unavailable_variants(cart)


def test_remove_unavailable_variants(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    cart.add(variant, 1)
    variant.stock.update(quantity=0)
    utils.remove_unavailable_variants(cart)
    assert len(cart) == 0


def test_check_product_availability_and_warn(
        monkeypatch, cart, product_in_stock):
    variant = product_in_stock.variants.get()
    cart.add(variant, 1)
    monkeypatch.setattr('django.contrib.messages.warning',
                        Mock(warning=Mock()))
    monkeypatch.setattr('saleor.cart.utils.contains_unavailable_variants',
                        Mock(return_value=False))

    utils.check_product_availability_and_warn(MagicMock(), cart)
    assert len(cart) == 1

    monkeypatch.setattr('saleor.cart.utils.contains_unavailable_variants',
                        Mock(return_value=True))
    monkeypatch.setattr('saleor.cart.utils.remove_unavailable_variants',
                        lambda c: c.add(variant, 0, replace=True))

    utils.check_product_availability_and_warn(MagicMock(), cart)
    assert len(cart) == 0


def test_add_to_cart_form():
    cart_lines = []
    cart = Mock(add=lambda variant, quantity: cart_lines.append(variant),
                get_line=Mock(return_value=Mock(quantity=1)))
    data = {'quantity': 1}
    form = forms.AddToCartForm(data=data, cart=cart, product=Mock())

    product_variant = Mock(check_quantity=Mock(return_value=None))
    form.get_variant = Mock(return_value=product_variant)

    assert form.is_valid()
    form.save()
    assert cart_lines == [product_variant]

    with pytest.raises(NotImplementedError):
        data = {'quantity': 1}
        form = forms.AddToCartForm(data=data, cart=cart, product=Mock())
        form.is_valid()


def test_form_when_variant_does_not_exist():
    cart_lines = []
    cart = Mock(add=lambda variant, quantity: cart_lines.append(Mock()),
                get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    form.get_variant = Mock(side_effect=ObjectDoesNotExist)
    assert not form.is_valid()


def test_add_to_cart_form_when_empty_stock():
    cart_lines = []
    cart = Mock(add=lambda variant, quantity: cart_lines.append(Mock()),
                get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    exception_mock = InsufficientStock(
        Mock(get_stock_quantity=Mock(return_value=1)))
    product_variant = Mock(check_quantity=Mock(side_effect=exception_mock))
    form.get_variant = Mock(return_value=product_variant)
    assert not form.is_valid()


def test_add_to_cart_form_when_insufficient_stock():
    cart_lines = []
    cart = Mock(add=lambda variant, quantity: cart_lines.append(variant),
                get_line=Mock(return_value=Mock(quantity=1)))

    form = forms.AddToCartForm(data={'quantity': 1}, cart=cart, product=Mock())
    exception_mock = InsufficientStock(
        Mock(get_stock_quantity=Mock(return_value=4)))
    product_variant = Mock(check_quantity=Mock(side_effect=exception_mock))
    form.get_variant = Mock(return_value=product_variant)
    assert not form.is_valid()


def test_replace_cart_line_form(cart, product_in_stock):
    variant = product_in_stock.variants.get()
    initial_quantity = 1
    replaced_quantity = 4

    cart.add(variant, initial_quantity)
    data = {'quantity': replaced_quantity}
    form = forms.ReplaceCartLineForm(data=data, cart=cart, variant=variant)
    assert form.is_valid()
    form.save()
    assert cart.quantity == replaced_quantity


def test_replace_cartline_form_when_insufficient_stock(
        monkeypatch, cart, product_in_stock):
    variant = product_in_stock.variants.get()
    initial_quantity = 1
    replaced_quantity = 4

    cart.add(variant, initial_quantity)
    exception_mock = InsufficientStock(
        Mock(get_stock_quantity=Mock(return_value=2)))
    monkeypatch.setattr('saleor.product.models.ProductVariant.check_quantity',
                        Mock(side_effect=exception_mock))
    data = {'quantity': replaced_quantity}
    form = forms.ReplaceCartLineForm(data=data, cart=cart, variant=variant)
    assert not form.is_valid()
    with pytest.raises(KeyError):
        form.save()
    assert cart.quantity == initial_quantity


def test_view_empty_cart(client, request_cart):
    response = client.get('/cart/')
    assert response.status_code == 200


def test_view_cart(client, product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.get('/cart/')
    assert response.status_code == 200


def test_view_update_cart_quantity(client, product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.post(
        '/cart/update/%s/' % (variant.pk,),
        {'quantity': 3},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    assert request_cart.quantity == 3


def test_view_invalid_update_cart(client, product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.post(
        '/cart/update/%s/' % (variant.pk,),
        {},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 400
    assert 'error' in resp_decoded.keys()
    assert request_cart.quantity == 1


def test_cart_page_without_openexchagerates(
        client, product_in_stock, request_cart, settings):
    settings.OPENEXCHANGERATES_API_KEY = None
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.get('/cart/')
    context = response.context
    assert context['local_cart_total'] is None


def test_cart_page_with_openexchagerates(
        client, monkeypatch, product_in_stock, request_cart, settings):
    settings.DEFAULT_CURRENCY = 'USD'
    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.get('/cart/')
    context = response.context
    assert context['local_cart_total'] is None
    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})
    response = client.get('/cart/')
    context = response.context
    assert context['local_cart_total'].currency == 'PLN'


def test_cart_summary_page(client, product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.get('/cart/summary/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    content = json.loads(content)
    assert content['quantity'] == request_cart.quantity
    cart_total = request_cart.get_total()
    assert content['total'] == currencyfmt(
        cart_total.gross, cart_total.currency)
    assert len(content['lines']) == 1
    cart_line = content['lines'][0]
    assert cart_line['variant'] == variant.name
    assert cart_line['quantity'] == 1


def test_cart_summary_page_empty_cart(client, request_cart):
    response = client.get('/cart/summary/')
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert json.loads(content) == {}
