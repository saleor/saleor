from unittest.mock import patch

from django.urls import reverse
from payments import FraudStatus, PaymentStatus

from saleor.account.models import User

from .utils import get_redirect_location


@patch('saleor.checkout.views.summary.send_order_confirmation')
def test_checkout_flow(
        mock_send_confirmation, request_cart_with_item, client,
        shipping_method):
    # Enter checkout
    checkout_index = client.get(reverse('checkout:index'), follow=True)
    # Checkout index redirects directly to shipping address step
    shipping_address = client.get(checkout_index.request['PATH_INFO'])

    # Enter shipping address data
    shipping_data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'street_address_1': 'Aleje Jerozolimskie 2',
        'street_address_2': '',
        'city': 'Warszawa',
        'city_area': '',
        'country_area': '',
        'postal_code': '00-374',
        'phone': '+48536984008',
        'country': 'PL'}
    shipping_response = client.post(
        shipping_address.request['PATH_INFO'], data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_page = client.get(shipping_response.request['PATH_INFO'])

    # Redirect to summary after shipping method selection
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    address_data = {'address': 'shipping_address'}
    summary_response = client.post(
        shipping_method_response.request['PATH_INFO'], data=address_data,
        follow=True)

    # After summary step, order is created and it waits for payment
    order = summary_response.context['order']

    # Select payment method
    payment_page = client.post(
        summary_response.request['PATH_INFO'], data={'method': 'default'},
        follow=True)
    assert len(payment_page.redirect_chain) == 1
    assert payment_page.status_code == 200
    # Go to payment details page, enter payment data
    payment_page_url = payment_page.redirect_chain[0][0]
    payment_data = {
        'status': PaymentStatus.PREAUTH,
        'fraud_status': FraudStatus.UNKNOWN,
        'gateway_response': '3ds-disabled',
        'verification_result': 'waiting'}
    payment_response = client.post(payment_page_url, data=payment_data)
    assert payment_response.status_code == 302
    payment_redirect = reverse(
        'order:payment-success', kwargs={'token': order.token})
    assert get_redirect_location(payment_response) == payment_redirect
    success_response = client.post(payment_redirect, data={'status': 'ok'})
    assert success_response.status_code == 302
    order_password = reverse(
        'order:checkout-success', kwargs={'token': order.token})
    assert get_redirect_location(success_response) == order_password
    mock_send_confirmation.delay.assert_called_once_with(order.pk)


def test_checkout_flow_authenticated_user(
        authorized_client, request_cart_with_item, customer_user,
        shipping_method):
    # Prepare some data
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    # Enter checkout
    # Checkout index redirects directly to shipping address step
    shipping_address = authorized_client.get(
        reverse('checkout:index'), follow=True)

    # Enter shipping address data
    shipping_data = {'address': customer_user.default_billing_address.pk}
    shipping_method_page = authorized_client.post(
        shipping_address.request['PATH_INFO'], data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = authorized_client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    payment_method_data = {'address': 'shipping_address'}
    payment_method_page = authorized_client.post(
        shipping_method_response.request['PATH_INFO'],
        data=payment_method_data, follow=True)

    # After summary step, order is created and it waits for payment
    order = payment_method_page.context['order']

    # Select payment method
    payment_page = authorized_client.post(
        payment_method_page.request['PATH_INFO'], data={'method': 'default'},
        follow=True)

    # Go to payment details page, enter payment data
    payment_data = {
        'status': PaymentStatus.PREAUTH,
        'fraud_status': FraudStatus.UNKNOWN,
        'gateway_response': '3ds-disabled',
        'verification_result': 'waiting'}
    payment_response = authorized_client.post(
        payment_page.request['PATH_INFO'], data=payment_data)

    assert payment_response.status_code == 302
    order_password = reverse(
        'order:payment-success', kwargs={'token': order.token})
    assert get_redirect_location(payment_response) == order_password

    # Assert that payment object was created and contains correct data
    payment = order.payments.all()[0]
    assert payment.total == order.total.gross.amount
    assert payment.tax == order.total.tax.amount
    assert payment.currency == order.total.currency
    assert payment.delivery == order.shipping_price.gross.amount
    assert len(payment.get_purchased_items()) == len(order.lines.all())


def test_address_without_shipping(request_cart_with_item, client, monkeypatch):
    monkeypatch.setattr(
        'saleor.checkout.core.Checkout.is_shipping_required', False)

    response = client.get(reverse('checkout:shipping-address'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:summary')


def test_shipping_method_without_shipping(
        request_cart_with_item, client, monkeypatch):
    monkeypatch.setattr('saleor.checkout.core.Checkout.is_shipping_required',
                        False)

    response = client.get(reverse('checkout:shipping-method'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:summary')


def test_shipping_method_without_address(request_cart_with_item, client):
    response = client.get(reverse('checkout:shipping-method'))
    assert response.status_code == 302
    assert (
        get_redirect_location(response) ==
        reverse('checkout:shipping-address'))


def test_summary_without_address(request_cart_with_item, client):
    response = client.get(reverse('checkout:summary'))
    assert response.status_code == 302
    assert (
        get_redirect_location(response) == reverse('checkout:shipping-method'))


def test_summary_without_shipping_method(
        request_cart_with_item, client, monkeypatch):
    # address test return true
    monkeypatch.setattr(
        'saleor.checkout.core.Checkout.email', True)

    response = client.get(reverse('checkout:summary'))
    assert response.status_code == 302
    assert (
        get_redirect_location(response) == reverse('checkout:shipping-method'))


def test_email_is_saved_in_order(
        authorized_client, customer_user, request_cart_with_item,
        shipping_method):
    # Prepare some data
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    # Enter checkout
    # Checkout index redirects directly to shipping address step
    shipping_address = authorized_client.get(
        reverse('checkout:index'), follow=True)

    # Enter shipping address data
    shipping_data = {'address': customer_user.default_billing_address.pk}
    shipping_method_page = authorized_client.post(
        shipping_address.request['PATH_INFO'], data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = authorized_client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    payment_method_data = {'address': 'shipping_address'}
    payment_method_page = authorized_client.post(
        shipping_method_response.request['PATH_INFO'],
        data=payment_method_data, follow=True)

    # After summary step, order is created and it waits for payment
    order = payment_method_page.context['order']
    assert order.user_email == customer_user.email


def test_voucher_invalid(
        client, request_cart_with_item, shipping_method, voucher):
    # related issues: #549 #544
    voucher.usage_limit = 3
    voucher.save()
    # Enter checkout
    checkout_index = client.get(reverse('checkout:index'), follow=True)
    # Checkout index redirects directly to shipping address step
    shipping_address = client.get(checkout_index.request['PATH_INFO'])

    # Enter shipping address data
    shipping_data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'street_address_1': 'Aleje Jerozolimskie 2',
        'street_address_2': '',
        'city': 'Warszawa',
        'city_area': '',
        'country_area': '',
        'postal_code': '00-374',
        'country': 'PL'}
    shipping_response = client.post(shipping_address.request['PATH_INFO'],
                                    data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_page = client.get(shipping_response.request['PATH_INFO'])

    # Redirect to summary after shipping method selection
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    url = shipping_method_response.request['PATH_INFO']
    discount_data = {'discount-voucher': voucher.code}
    voucher_response = client.post(
        '{url}?next={url}'.format(url=url), follow=True, data=discount_data,
        HTTP_REFERER=url)
    assert voucher_response.context['checkout'].voucher_code == voucher.code
    voucher.used = 3
    voucher.save()
    address_data = {'address': 'shipping_address'}
    assert url == reverse('checkout:summary')
    summary_response = client.post(url, data=address_data, follow=True)
    assert summary_response.context['checkout'].voucher_code is None

    summary_response = client.post(url, data=address_data, follow=True)
    assert summary_response.context['order'].voucher is None


def test_voucher_code_invalid(
        client, request_cart_with_item, shipping_method):
    # Enter checkout
    checkout_index = client.get(reverse('checkout:index'), follow=True)
    # Checkout index redirects directly to shipping address step
    shipping_address = client.get(checkout_index.request['PATH_INFO'])

    # Enter shipping address data
    shipping_data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'street_address_1': 'Aleje Jerozolimskie 2',
        'street_address_2': '',
        'city': 'Warszawa',
        'city_area': '',
        'country_area': '',
        'postal_code': '00-374',
        'country': 'PL'}
    shipping_response = client.post(shipping_address.request['PATH_INFO'],
                                    data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_page = client.get(shipping_response.request['PATH_INFO'])

    # Redirect to summary after shipping method selection
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    url = shipping_method_response.request['PATH_INFO']
    discount_data = {'discount-voucher': 'invalid-code'}
    voucher_response = client.post(
        '{url}?next={url}'.format(url=url), follow=True, data=discount_data,
        HTTP_REFERER=url)
    assert voucher_response.status_code == 200
    assert 'voucher' in voucher_response.context['voucher_form'].errors
    assert voucher_response.context['checkout'].voucher_code is None


def test_remove_voucher(
        client, request_cart_with_item, shipping_method, voucher):
    # Enter checkout
    checkout_index = client.get(reverse('checkout:index'), follow=True)
    # Checkout index redirects directly to shipping address step
    shipping_address = client.get(checkout_index.request['PATH_INFO'])

    # Enter shipping address data
    shipping_data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'street_address_1': 'Aleje Jerozolimskie 2',
        'street_address_2': '',
        'city': 'Warszawa',
        'city_area': '',
        'country_area': '',
        'postal_code': '00-374',
        'country': 'PL'}
    shipping_response = client.post(shipping_address.request['PATH_INFO'],
                                    data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_page = client.get(shipping_response.request['PATH_INFO'])

    # Redirect to summary after shipping method selection
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    url = shipping_method_response.request['PATH_INFO']
    discount_data = {'discount-voucher': voucher.code}
    voucher_response = client.post(
        '{url}?next={url}'.format(url=url), follow=True, data=discount_data,
        HTTP_REFERER=url)
    assert voucher_response.context['checkout'].voucher_code is not None
    # Remove voucher from checkout
    voucher_response = client.post(
        reverse('checkout:remove-voucher'), follow=True, HTTP_REFERER=url)
    assert voucher_response.status_code == 200
    assert voucher_response.context['checkout'].voucher_code is None


def test_language_is_saved_in_order(
        authorized_client, customer_user, request_cart_with_item, settings,
        shipping_method):
    # Prepare some data
    settings.LANGUAGE_CODE = 'en'
    user_language = 'fr'
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    # Set user's language to fr
    authorized_client.cookies[settings.LANGUAGE_COOKIE_NAME] = user_language
    authorized_client.post(reverse('set_language'), data={'language': 'fr'})
    # Enter checkout
    # Checkout index redirects directly to shipping address step
    shipping_address = authorized_client.get(
        reverse('checkout:index'), follow=True,
        HTTP_ACCEPT_LANGUAGE=user_language)

    # Enter shipping address data
    shipping_data = {'address': customer_user.default_billing_address.pk}
    shipping_method_page = authorized_client.post(
        shipping_address.request['PATH_INFO'], data=shipping_data, follow=True,
        HTTP_ACCEPT_LANGUAGE=user_language)

    # Select shipping method
    shipping_method_data = {
        'method': shipping_method.price_per_country.first().pk}
    shipping_method_response = authorized_client.post(
        shipping_method_page.request['PATH_INFO'], data=shipping_method_data,
        follow=True, HTTP_ACCEPT_LANGUAGE=user_language)

    # Summary page asks for Billing address, default is the same as shipping
    payment_method_data = {'address': 'shipping_address'}
    payment_method_page = authorized_client.post(
        shipping_method_response.request['PATH_INFO'],
        data=payment_method_data, follow=True,
        HTTP_ACCEPT_LANGUAGE=user_language)

    # After summary step, order is created and it waits for payment
    order = payment_method_page.context['order']
    assert order.language_code == user_language


def test_create_user_after_order(order, client):
    order.user_email = 'hello@mirumee.com'
    order.save()
    assert not User.objects.filter(email='hello@mirumee.com').exists()
    data = {'password': 'password'}
    url = reverse('order:checkout-success', kwargs={'token': order.token})
    response = client.post(url, data=data)
    redirect_location = get_redirect_location(response)
    detail_url = reverse('order:details', kwargs={'token': order.token})
    assert redirect_location == detail_url
    user = User.objects.filter(email='hello@mirumee.com')
    assert user.exists()
    user = user.first()
    assert user.orders.filter(token=order.token).exists()
