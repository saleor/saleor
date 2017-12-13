from django.urls import reverse

from saleor.shipping.models import ShippingMethod, ShippingMethodCountry


def test_shipping_method_list(admin_client, shipping_method):
    url = reverse('dashboard:shipping-methods')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_shipping_method_add(admin_client):
    assert len(ShippingMethod.objects.all()) == 0
    url = reverse('dashboard:shipping-method-add')
    data = {'name': 'Zium', 'description': 'Fastest zium'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethod.objects.all()) == 1


def test_shipping_method_add_not_valid(admin_client):
    assert len(ShippingMethod.objects.all()) == 0
    url = reverse('dashboard:shipping-method-add')
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethod.objects.all()) == 0


def test_shipping_method_edit(admin_client, shipping_method):
    assert len(ShippingMethod.objects.all()) == 1
    url = reverse('dashboard:shipping-method-update',
                  kwargs={'pk': shipping_method.pk})
    data = {'name': 'Flash', 'description': 'In a flash!'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethod.objects.all()) == 1
    assert ShippingMethod.objects.all()[0].name == 'Flash'


def test_shipping_method_detail(admin_client, shipping_method):
    assert len(ShippingMethod.objects.all()) == 1
    url = reverse('dashboard:shipping-method-detail',
                  kwargs={'pk': shipping_method.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200


def test_shipping_method_delete(admin_client, shipping_method):
    assert len(ShippingMethod.objects.all()) == 1
    url = reverse('dashboard:shipping-method-delete',
                  kwargs={'pk': shipping_method.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethod.objects.all()) == 0


def test_shipping_method_country_add(admin_client, shipping_method):
    assert len(ShippingMethodCountry.objects.all()) == 1
    url = reverse('dashboard:shipping-method-country-add',
                  kwargs={'shipping_method_pk': shipping_method.pk})
    data = {'country_code': 'FR', 'price': '50',
            'shipping_method': shipping_method.pk}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethodCountry.objects.all()) == 2


def test_shipping_method_country_add_not_valid(admin_client, shipping_method):
    assert len(ShippingMethodCountry.objects.all()) == 1
    url = reverse('dashboard:shipping-method-country-add',
                  kwargs={'shipping_method_pk': shipping_method.pk})
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethodCountry.objects.all()) == 1


def test_shipping_method_country_edit(admin_client, shipping_method):
    assert len(ShippingMethodCountry.objects.all()) == 1
    country = shipping_method.price_per_country.all()[0]
    assert country.price.gross == 10
    url = reverse('dashboard:shipping-method-country-edit',
                  kwargs={'shipping_method_pk': shipping_method.pk,
                          'country_pk': country.pk})
    data = {'country_code': '', 'price': '50',
            'shipping_method': shipping_method.pk}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethodCountry.objects.all()) == 1
    assert shipping_method.price_per_country.all()[0].price.gross == 50


def test_shipping_method_country_delete(admin_client, shipping_method):
    assert len(ShippingMethodCountry.objects.all()) == 1
    country = shipping_method.price_per_country.all()[0]
    url = reverse('dashboard:shipping-method-country-delete',
                  kwargs={'shipping_method_pk': shipping_method.pk,
                          'country_pk': country.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert len(ShippingMethodCountry.objects.all()) == 0
