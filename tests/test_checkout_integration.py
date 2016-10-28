from django.core.urlresolvers import reverse

from saleor.order.models import Order
from saleor.registration.models import EmailChangeRequest
from saleor.userprofile.models import User
from tests.utils import get_redirect_location


def test_checkout_flow(request_cart_with_item, client, shipping_method):  # pylint: disable=W0613
    """
    Basic test case that confirms if core checkout flow works
    """

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
    shipping_method_data = {'method': shipping_method.pk}
    shipping_method_response = client.post(shipping_method_page.request['PATH_INFO'],
                                           data=shipping_method_data, follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    address_data = {'address': 'shipping_address'}
    summary_response = client.post(shipping_method_response.request['PATH_INFO'],
                                   data=address_data, follow=True)

    # After summary step, order is created and it waits for payment
    order = summary_response.context['order']

    # Select payment method
    payment_page = client.post(summary_response.request['PATH_INFO'],
                               data={'method': 'default'}, follow=True)
    assert len(payment_page.redirect_chain) == 1
    assert payment_page.status_code == 200
    # Go to payment details page, enter payment data
    payment_page_url = payment_page.redirect_chain[0][0]
    payment_data = {
        'status': 'preauth',
        'fraud_status': 'unknown',
        'gateway_response': '3ds-disabled',
        'verification_result': 'waiting'}
    payment_response = client.post(payment_page_url, data=payment_data)
    assert payment_response.status_code == 302
    order_details = reverse('order:details', kwargs={'token': order.token})
    assert get_redirect_location(payment_response) == order_details


def test_checkout_flow_authenticated_user(authorized_client, billing_address, request_cart_with_item,
                                          normal_user, shipping_method):
    """
    Checkout with authenticated user and previously saved address
    """
    # Prepare some data
    normal_user.addresses.add(billing_address)
    request_cart_with_item.user = normal_user
    request_cart_with_item.save()

    # Enter checkout
    # Checkout index redirects directly to shipping address step
    shipping_address = authorized_client.get(reverse('checkout:index'), follow=True)

    # Enter shipping address data
    shipping_data = {'address': billing_address.pk}
    shipping_method_page = authorized_client.post(shipping_address.request['PATH_INFO'],
                                                  data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_data = {'method': shipping_method.pk}
    shipping_method_response = authorized_client.post(shipping_method_page.request['PATH_INFO'],
                                                      data=shipping_method_data, follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    payment_method_data = {'address': 'shipping_address'}
    payment_method_page = authorized_client.post(shipping_method_response.request['PATH_INFO'],
                                                 data=payment_method_data, follow=True)

    # After summary step, order is created and it waits for payment
    order = payment_method_page.context['order']

    # Select payment method
    payment_page = authorized_client.post(payment_method_page.request['PATH_INFO'],
                                          data={'method': 'default'}, follow=True)

    # Go to payment details page, enter payment data
    payment_data = {
        'status': 'preauth',
        'fraud_status': 'unknown',
        'gateway_response': '3ds-disabled',
        'verification_result': 'waiting'}
    payment_response = authorized_client.post(payment_page.request['PATH_INFO'],
                                              data=payment_data)

    assert payment_response.status_code == 302
    order_details = reverse('order:details', kwargs={'token': order.token})
    assert get_redirect_location(payment_response) == order_details


def test_address_without_shipping(request_cart_with_item, client, monkeypatch):  # pylint: disable=W0613
    """
    user tries to get shipping address step in checkout without shipping -
     if is redirected to summary step
    """

    monkeypatch.setattr('saleor.checkout.core.Checkout.is_shipping_required',
                        False)

    response = client.get(reverse('checkout:shipping-address'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:summary')


def test_shipping_method_without_shipping(request_cart_with_item, client, monkeypatch):  # pylint: disable=W0613
    """
    user tries to get shipping method step in checkout without shipping -
     if is redirected to summary step
    """

    monkeypatch.setattr('saleor.checkout.core.Checkout.is_shipping_required',
                        False)

    response = client.get(reverse('checkout:shipping-method'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:summary')


def test_shipping_method_without_address(request_cart_with_item, client):  # pylint: disable=W0613
    """
    user tries to get shipping method step without saved shipping address -
     if is redirected to shipping address step
    """

    response = client.get(reverse('checkout:shipping-method'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:shipping-address')


def test_summary_without_address(request_cart_with_item, client):  # pylint: disable=W0613
    """
    user tries to get summary step without saved shipping method -
     if is redirected to shipping method step
    """

    response = client.get(reverse('checkout:summary'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:shipping-method')


def test_summary_without_shipping_method(request_cart_with_item, client, monkeypatch):  # pylint: disable=W0613
    """
    user tries to get summary step without saved shipping method -
     if is redirected to shipping method step
    """
    #address test return true
    monkeypatch.setattr('saleor.checkout.core.Checkout.email',
                        True)

    response = client.get(reverse('checkout:summary'))
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('checkout:shipping-method')


def test_client_login(request_cart_with_item, client, admin_user):
    data = {
        'username': admin_user.email,
        'password': 'password'
    }
    response = client.post(reverse('registration:login'), data=data)
    assert response.status_code == 302
    assert get_redirect_location(response) == '/'
    response = client.get(reverse('checkout:shipping-address'))
    assert response.context['checkout'].cart.token == request_cart_with_item.token


def test_email_is_saved_in_order(authorized_client, billing_address, normal_user,  # pylint: disable=R0914
                                 request_cart_with_item, shipping_method):
    """
    authorized user change own email after checkout - if is not changed in order
    """
    # Prepare some data
    normal_user.addresses.add(billing_address)
    request_cart_with_item.user = normal_user
    request_cart_with_item.save()

    # Enter checkout
    # Checkout index redirects directly to shipping address step
    shipping_address = authorized_client.get(reverse('checkout:index'), follow=True)

    # Enter shipping address data
    shipping_data = {'address': billing_address.pk}
    shipping_method_page = authorized_client.post(shipping_address.request['PATH_INFO'],
                                                  data=shipping_data, follow=True)

    # Select shipping method
    shipping_method_data = {'method': shipping_method.pk}
    shipping_method_response = authorized_client.post(shipping_method_page.request['PATH_INFO'],
                                                      data=shipping_method_data, follow=True)

    # Summary page asks for Billing address, default is the same as shipping
    payment_method_data = {'address': 'shipping_address'}
    payment_method_page = authorized_client.post(shipping_method_response.request['PATH_INFO'],
                                                 data=payment_method_data, follow=True)

    # After summary step, order is created and it waits for payment
    order = payment_method_page.context['order']
    assert order.user_email == normal_user.email

    # User change email

    authorized_client.post(reverse('registration:request_email_change'),
                           data={'email': 'new@example.com'})

    #get token:
    token = EmailChangeRequest.objects.get(email='new@example.com').token
    url = reverse('registration:change_email', args=[token])
    authorized_client.get(url)

    updated_user = User.objects.get(pk=normal_user.pk)
    order = Order.objects.get(pk=order.pk)
    assert updated_user.email != normal_user.email
    assert updated_user.email == 'new@example.com'
    assert order.user_email == normal_user.email
