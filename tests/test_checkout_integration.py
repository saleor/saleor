import pytest
from django.contrib.sites.models import Site
from django.core import signing
from django.core.urlresolvers import reverse

from saleor.cart.models import Cart
from saleor.order import Status as OrderStatus
from saleor.order.models import Order
from saleor.shipping.models import ShippingMethod

# Resolve urls
urls = {
    'cart': reverse('cart:index'),
    'checkout_index': reverse('checkout:index'),
    'checkout_shipping_address': reverse('checkout:shipping-address'),
    'checkout_shipping_method': reverse('checkout:shipping-method'),
    'checkout_summary': reverse('checkout:summary')}


@pytest.fixture
def client_with_cart(product_in_stock, client):
    variant = product_in_stock.variants.get()
    # Prepare some data
    base_cart = Cart.objects.create()
    base_cart.add(variant)

    value = signing.get_cookie_signer(salt=Cart.COOKIE_NAME).sign(base_cart.token)
    client.cookies[Cart.COOKIE_NAME] = value
    client.cart = base_cart
    return client


def assert_redirect(response, expected_url):
    assert response.status_code == 302
    # Due to Django 1.8 compatibility, we have to handle both cases
    location = response['Location']
    if location.startswith('http'):
        location = location.split('http://testserver')[1]
    assert location == expected_url


def test_checkout_flow(product_in_stock, client):
    """
    Basic test case that confirms if core checkout flow works
    """
    variant = product_in_stock.variants.get()
    # Prepare some data
    cart = Cart.objects.create()
    cart.add(variant)
    shipping_method = ShippingMethod.objects.create(name='DHL')
    shipping_variant = shipping_method.price_per_country.create(price=10)


    # This is anonymous checkout, so cart token in stored in signed cookie
    value = signing.get_cookie_signer(salt=Cart.COOKIE_NAME).sign(cart.token)
    client.cookies[Cart.COOKIE_NAME] = value

    # Go to cart page
    cart_page = client.get(urls['cart'])
    cart_lines = cart_page.context['cart_lines']
    assert len(cart_lines) == cart.lines.count()
    assert cart_lines[0]['variant'] == variant
    # Enter checkout
    checkout_index = client.get(urls['checkout_index'])
    # Checkout index redirects directly to shipping address step
    assert_redirect(checkout_index, urls['checkout_shipping_address'])
    shipping_address = client.get(urls['checkout_shipping_address'])
    assert shipping_address.status_code == 200
    # Enter shipping address data
    shipping_data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'street_address_1': 'Some street',
        'street_address_2': '',
        'city': 'Somewhere',
        'city_area': '',
        'country_area': '',
        'postal_code': '50-123',
        'country': 'PL'}
    shipping_response = client.post(
        urls['checkout_shipping_address'], data=shipping_data)
    # Select shipping method
    assert_redirect(shipping_response, urls['checkout_shipping_method'])
    shipping_method_page = client.get(urls['checkout_shipping_method'])
    assert shipping_method_page.status_code == 200
    # Redirect to summary after shipping method selection
    shipping_method_response = client.post(
        urls['checkout_shipping_method'], data={'method': shipping_method.pk})
    assert_redirect(shipping_method_response, urls['checkout_summary'])
    # Summary page asks for Billing address, default is the same as shipping
    summary_response = client.post(urls['checkout_summary'],
                                   data={'address': 'shipping_address'})
    # After summary step, order is created and it waits for payment
    order = Order.objects.latest('pk')
    order_payment_url = reverse('order:payment', kwargs={'token': order.token})
    assert_redirect(summary_response, order_payment_url)
    payment_method_page = client.get(order_payment_url)
    assert payment_method_page.status_code == 200
    # Select payment method
    payment_page = client.post(order_payment_url, data={'method': 'default'},
                               follow=True)
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
    # Target page contains full URL with domain from Site object
    site = Site.objects.get_current()
    order_details = reverse('order:details', kwargs={'token': order.token})
    expected_url = 'http://%s%s' % (site, order_details)
    assert payment_response['Location'] == expected_url
    order_details_page = client.get(order_details)
    assert order_details_page.status_code == 200
    # Check if order has correct totals and payments
    expected_total = variant.get_price() + shipping_variant.price
    assert order.total == expected_total
    assert order.payments.exists()
    payment = order.payments.latest('pk')
    assert payment.status == 'preauth'
    assert order.status == OrderStatus.NEW


def test_address_without_shipping(client_with_cart, monkeypatch):
    """
    user tries to get shipping address step in checkout without shipping -
     if is redirected to summary step
    """

    monkeypatch.setattr('saleor.checkout.core.Checkout.is_shipping_required',
                        False)

    response = client_with_cart.get(urls['checkout_shipping_address'])
    assert response.status_code == 302
    assert response.url == urls['checkout_summary']


def test_shipping_method_without_shipping(client_with_cart, monkeypatch):
    """
    user tries to get shipping method step in checkout without shipping -
     if is redirected to summary step
    """

    monkeypatch.setattr('saleor.checkout.core.Checkout.is_shipping_required',
                        False)

    response = client_with_cart.get(urls['checkout_shipping_method'])
    assert response.status_code == 302
    assert response.url == urls['checkout_summary']


def test_shipping_method_without_address(client_with_cart):
    """
    user tries to get shipping method step without saved shipping address -
     if is redirected to shipping address step
    """

    response = client_with_cart.get(urls['checkout_shipping_method'])
    assert response.status_code == 302
    assert response.url == urls['checkout_shipping_address']


def test_summary_without_address(client_with_cart):
    """
    user tries to get summary step without saved shipping method -
     if is redirected to shipping method step
    """

    response = client_with_cart.get(urls['checkout_summary'])
    assert response.status_code == 302
    assert response.url == urls['checkout_shipping_method']


def test_summary_without_shipping_method(client_with_cart, monkeypatch):
    """
    user tries to get summary step without saved shipping method -
     if is redirected to shipping method step
    """
    #address test return true
    monkeypatch.setattr('saleor.checkout.core.Checkout.email',
                        True)

    response = client_with_cart.get(urls['checkout_summary'])
    assert response.status_code == 302
    assert response.url == urls['checkout_shipping_method']


def test_client_login(client_with_cart, admin_user, monkeypatch):
    data = {
        'username': admin_user.email,
        'password': 'password'
    }
    url = '{url}?next={next}'.format(url=reverse('registration:login'),
                                     next=urls['checkout_index'])

    assert Cart.objects.filter(user=admin_user).count() == 0

    response = client_with_cart.post(url, data=data)
    assert response.status_code == 302
    assert response.url == urls['checkout_index'] #success!

    assert Cart.objects.filter(user=admin_user).count() == 1
    assert Cart.objects.all()[0].token == client_with_cart.cart.token
