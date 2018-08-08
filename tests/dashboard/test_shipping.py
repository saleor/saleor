from django.urls import reverse
from prices import Money

from saleor.shipping.models import ShippingZone, ShippingRate


def test_shipping_method_list(admin_client, shipping_method):
    url = reverse('dashboard:shipping-methods')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_shipping_method_add(admin_client):
    assert ShippingZone.objects.count() == 0
    url = reverse('dashboard:shipping-method-add')
    data = {'name': 'Zium', 'description': 'Fastest zium'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 1


def test_shipping_method_add_not_valid(admin_client):
    assert ShippingZone.objects.count() == 0
    url = reverse('dashboard:shipping-method-add')
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 0


def test_shipping_method_edit(admin_client, shipping_method):
    assert ShippingZone.objects.count() == 1
    url = reverse('dashboard:shipping-method-update',
                  kwargs={'pk': shipping_method.pk})
    data = {'name': 'Flash', 'description': 'In a flash!'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 1
    assert ShippingZone.objects.all()[0].name == 'Flash'


def test_shipping_method_details(admin_client, shipping_method):
    assert ShippingZone.objects.count() == 1
    url = reverse('dashboard:shipping-method-details',
                  kwargs={'pk': shipping_method.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200


def test_shipping_method_delete(admin_client, shipping_method):
    assert ShippingZone.objects.count() == 1
    url = reverse('dashboard:shipping-method-delete',
                  kwargs={'pk': shipping_method.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 0


def test_shipping_rate_add(admin_client, shipping_method):
    assert ShippingRate.objects.count() == 1
    url = reverse('dashboard:shipping-rate-add',
                  kwargs={'shipping_method_pk': shipping_method.pk})
    data = {'country_code': 'FR', 'price': '50',
            'shipping_method': shipping_method.pk}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingRate.objects.count() == 2


def test_shipping_rate_add_not_valid(admin_client, shipping_method):
    assert ShippingRate.objects.count() == 1
    url = reverse('dashboard:shipping-rate-add',
                  kwargs={'shipping_method_pk': shipping_method.pk})
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingRate.objects.count() == 1


def test_shipping_rate_edit(admin_client, shipping_method):
    assert ShippingRate.objects.count() == 1
    country = shipping_method.shipping_methods.all()[0]
    assert country.price == Money(10, 'USD')
    url = reverse('dashboard:shipping-rate-edit',
                  kwargs={'shipping_method_pk': shipping_method.pk,
                          'rate_pk': country.pk})
    data = {'country_code': '', 'price': '50',
            'shipping_method': shipping_method.pk}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingRate.objects.count() == 1

    shipping_price = shipping_method.shipping_methods.all()[0].price
    assert shipping_price == Money(50, 'USD')


def test_shipping_rate_delete(admin_client, shipping_method):
    assert ShippingRate.objects.count() == 1
    country = shipping_method.shipping_methods.all()[0]
    url = reverse('dashboard:shipping-rate-delete',
                  kwargs={'shipping_method_pk': shipping_method.pk,
                          'rate_pk': country.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert ShippingRate.objects.count() == 0
