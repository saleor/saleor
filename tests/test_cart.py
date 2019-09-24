import json
from unittest.mock import MagicMock, Mock
from uuid import uuid4

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from django.urls import reverse
from measurement.measures import Weight
from prices import Money, TaxedMoney

from saleor.checkout import forms, utils
from saleor.checkout.context_processors import checkout_counter
from saleor.checkout.models import Checkout
from saleor.checkout.utils import (
    add_variant_to_checkout,
    change_checkout_user,
    find_open_checkout_for_user,
    get_shipping_price_estimate,
)
from saleor.checkout.views import clear_checkout, update_checkout_line
from saleor.core.exceptions import InsufficientStock
from saleor.discount.models import Sale
from saleor.product.models import Category


@pytest.fixture()
def checkout_request_factory(rf, monkeypatch):
    def create_request(user=None, token=None):
        request = rf.get(reverse("home"))
        if user is None:
            request.user = AnonymousUser()
        else:
            request.user = user
        request.discounts = Sale.objects.all()
        request.extensions = None
        monkeypatch.setattr(request, "get_signed_cookie", Mock(return_value=token))
        return request

    return create_request


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


def test_get_or_create_checkout_from_request(
    checkout_request_factory, monkeypatch, customer_user
):
    token = uuid4()
    queryset = Checkout.objects.all()
    request = checkout_request_factory(user=customer_user, token=token)
    user_checkout = Checkout(user=customer_user)
    anonymous_checkout = Checkout()
    mock_get_for_user = Mock(return_value=(user_checkout, False))
    mock_get_for_anonymous = Mock(return_value=anonymous_checkout)
    monkeypatch.setattr("saleor.checkout.utils.get_user_checkout", mock_get_for_user)
    monkeypatch.setattr(
        "saleor.checkout.utils.get_or_create_anonymous_checkout_from_token",
        mock_get_for_anonymous,
    )
    returned_checkout = utils.get_or_create_checkout_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset, auto_create=True)
    assert returned_checkout == user_checkout

    request = checkout_request_factory(user=None, token=token)
    returned_checkout = utils.get_or_create_checkout_from_request(request, queryset)
    mock_get_for_anonymous.assert_called_once_with(token, queryset)
    assert returned_checkout == anonymous_checkout


def test_get_checkout_from_request(
    monkeypatch, customer_user, checkout_request_factory
):
    queryset = Checkout.objects.all()
    token = uuid4()
    request = checkout_request_factory(user=customer_user, token=token)

    user_checkout = Checkout(user=customer_user)
    mock_get_for_user = Mock(return_value=(user_checkout, False))
    monkeypatch.setattr("saleor.checkout.utils.get_user_checkout", mock_get_for_user)
    returned_checkout = utils.get_checkout_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_checkout == user_checkout

    mock_get_for_user = Mock(return_value=(None, False))
    monkeypatch.setattr("saleor.checkout.utils.get_user_checkout", mock_get_for_user)
    returned_checkout = utils.get_checkout_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert not Checkout.objects.filter(token=returned_checkout.token).exists()

    anonymous_checkout = Checkout()
    mock_get_for_anonymous = Mock(return_value=anonymous_checkout)
    monkeypatch.setattr(
        "saleor.checkout.utils.get_anonymous_checkout_from_token",
        mock_get_for_anonymous,
    )
    request = checkout_request_factory(user=None, token=token)
    returned_checkout = utils.get_checkout_from_request(request, queryset)
    mock_get_for_user.assert_called_once_with(customer_user, queryset)
    assert returned_checkout == anonymous_checkout

    mock_get_for_anonymous = Mock(return_value=None)
    monkeypatch.setattr(
        "saleor.checkout.utils.get_anonymous_checkout_from_token",
        mock_get_for_anonymous,
    )
    returned_checkout = utils.get_checkout_from_request(request, queryset)
    assert not Checkout.objects.filter(token=returned_checkout.token).exists()


def test_find_and_assign_anonymous_checkout(anonymous_checkout, customer_user, client):
    checkout_token = anonymous_checkout.token
    # Anonymous user has a checkout with token stored in cookie
    value = signing.get_cookie_signer(salt=utils.COOKIE_NAME).sign(checkout_token)
    client.cookies[utils.COOKIE_NAME] = value
    # Anonymous logs in
    response = client.post(
        reverse("account:login"),
        {"username": customer_user.email, "password": "password"},
        follow=True,
    )
    assert response.context["user"] == customer_user
    # User should have only one checkout, the same as he had previously in
    # anonymous session
    authenticated_user_checkouts = customer_user.checkouts.all()
    assert authenticated_user_checkouts.count() == 1
    assert authenticated_user_checkouts[0].token == checkout_token


def test_login_without_a_checkout(customer_user, client):
    assert utils.COOKIE_NAME not in client.cookies
    response = client.post(
        reverse("account:login"),
        {"username": customer_user.email, "password": "password"},
        follow=True,
    )
    assert response.context["user"] == customer_user
    authenticated_user_checkouts = customer_user.checkouts.all()
    assert authenticated_user_checkouts.count() == 0


def test_login_with_incorrect_cookie_token(customer_user, client):
    value = signing.get_cookie_signer(salt=utils.COOKIE_NAME).sign("incorrect")
    client.cookies[utils.COOKIE_NAME] = value
    response = client.post(
        reverse("account:login"),
        {"username": customer_user.email, "password": "password"},
        follow=True,
    )
    assert response.context["user"] == customer_user
    authenticated_user_checkouts = customer_user.checkouts.all()
    assert authenticated_user_checkouts.count() == 0


def test_find_and_assign_anonymous_checkout_and_close_opened(
    customer_user, user_checkout, anonymous_checkout, checkout_request_factory
):
    token = anonymous_checkout.token
    token_user = user_checkout.token
    request = checkout_request_factory(user=customer_user, token=token)
    utils.find_and_assign_anonymous_checkout()(
        lambda request: Mock(delete_cookie=lambda name: None)
    )(request)
    token_checkout = Checkout.objects.filter(token=token).first()
    user_checkout = Checkout.objects.filter(token=token_user).first()
    assert token_checkout is not None
    assert token_checkout.user.pk == customer_user.pk
    assert not user_checkout


def test_adding_without_checking(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1000, check_quantity=False)
    assert len(checkout) == 1


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
    subtotal = Money("30.00", "USD")
    assert checkout.get_subtotal() == subtotal


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


def test_view_empty_checkout(client, request_checkout):
    response = client.get(reverse("checkout:index"))
    assert response.status_code == 200


def test_view_checkout(client, request_checkout_with_item):
    response = client.get(reverse("checkout:index"))
    response_checkout_line = response.context[0]["checkout_lines"][0]
    checkout_line = request_checkout_with_item.lines.first()
    assert response.status_code == 200
    assert not response_checkout_line["get_total"].tax.amount
    total = checkout_line.get_total()
    assert response_checkout_line["get_total"] == TaxedMoney(total, total)


def test_view_update_checkout_quantity(client, request_checkout_with_item, monkeypatch):
    monkeypatch.setattr(
        "saleor.checkout.views.to_local_currency", lambda price, currency: price
    )
    variant = request_checkout_with_item.lines.get().variant
    response = client.post(
        reverse("checkout:update-line", kwargs={"variant_id": variant.pk}),
        data={"quantity": 3},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    assert request_checkout_with_item.quantity == 3


def test_view_invalid_update_checkout(client, request_checkout_with_item):
    variant = request_checkout_with_item.lines.get().variant
    response = client.post(
        reverse("checkout:update-line", kwargs={"variant_id": variant.pk}),
        data={},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    resp_decoded = json.loads(response.content.decode("utf-8"))
    assert response.status_code == 400
    assert "error" in resp_decoded.keys()
    assert request_checkout_with_item.quantity == 1


def test_view_invalid_variant_update_checkout(client, checkout_with_single_item):
    response = client.post(
        reverse("checkout:update-line", kwargs={"variant_id": "123"}),
        data={},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 404


def test_checkout_page_without_openexchagerates(
    client, checkout_with_single_item, settings
):
    settings.OPENEXCHANGERATES_API_KEY = None
    response = client.get(reverse("checkout:index"))
    context = response.context
    assert context["local_checkout_total"] is None


def test_checkout_page_with_openexchagerates(
    client, monkeypatch, checkout_with_single_item, settings
):
    settings.DEFAULT_COUNTRY = "PL"
    settings.OPENEXCHANGERATES_API_KEY = "fake-key"
    response = client.get(reverse("checkout:index"))
    context = response.context
    assert context["local_checkout_total"] is None
    monkeypatch.setattr(
        "django_prices_openexchangerates.models.get_rates",
        lambda c: {"PLN": Mock(rate=2)},
    )
    response = client.get(reverse("checkout:index"))
    context = response.context
    assert context["local_checkout_total"].currency == "PLN"


def test_checkout_summary_page(settings, client, request_checkout_with_item):
    settings.DEFAULT_COUNTRY = "PL"
    response = client.get(reverse("checkout:dropdown"))
    assert response.status_code == 200
    content = response.context
    assert content["quantity"] == request_checkout_with_item.quantity
    checkout_total = request_checkout_with_item.get_subtotal()
    assert content["total"] == TaxedMoney(checkout_total, checkout_total)
    assert len(content["lines"]) == 1
    checkout_line = content["lines"][0]
    variant = request_checkout_with_item.lines.get().variant
    assert checkout_line["variant"] == variant
    assert checkout_line["quantity"] == 1


def test_checkout_summary_page_empty_checkout(client, request_checkout):
    response = client.get(reverse("checkout:dropdown"))
    assert response.status_code == 200
    data = response.context
    assert data["quantity"] == 0


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


def test_update_view_must_be_ajax(customer_user, rf):
    request = rf.post(reverse("home"))
    request.user = customer_user
    request.discounts = None
    result = update_checkout_line(request, 1)
    assert result.status_code == 302


def test_update_checkout_line_qunatity_zero(
    request_checkout_with_item, client, product
):
    variant = product.variants.filter().first()
    data = {"quantity": 0}
    # response = client.post(API_PATH, data, content_type="application/json")
    response = client.post(
        reverse("checkout:update-line", kwargs={"variant_id": variant.id}),
        data=data,
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert response.status_code == 200
    expected_response = {
        "variantId": str(variant.id),
        "subtotal": "$0.00",
        "total": "$0.00",
        "checkout": {"numItems": 0, "numLines": 0},
    }
    data = response.json()
    assert data == expected_response


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


def test_clear_checkout_must_be_ajax(rf, customer_user):
    request = rf.post(reverse("home"))
    request.user = customer_user
    request.discounts = None
    response = clear_checkout(request)
    assert response.status_code == 302


def test_clear_checkout(request_checkout_with_item, client):
    response = client.post(
        reverse("checkout:clear"), data={}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert response.status_code == 200
    assert len(request_checkout_with_item.lines.all()) == 0


def test_get_total_weight(checkout_with_item):
    line = checkout_with_item.lines.first()
    variant = line.variant
    variant.weight = Weight(kg=10)
    variant.save()
    line.quantity = 6
    line.save()
    assert checkout_with_item.get_total_weight() == Weight(kg=60)
