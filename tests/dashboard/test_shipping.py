import pytest
from django.urls import reverse
from prices import Money

from saleor.account.i18n import COUNTRY_CHOICES
from saleor.core.weight import WeightUnits
from saleor.dashboard.shipping.forms import (
    PriceShippingMethodForm, ShippingZoneForm, WeightShippingMethodForm,
    currently_used_countries, default_shipping_zone_exists,
    get_available_countries)
from saleor.shipping import ShippingMethodType
from saleor.shipping.models import ShippingMethod, ShippingZone


def test_default_shipping_zone_exists(shipping_zone):
    shipping_zone.default = True
    shipping_zone.save()
    assert default_shipping_zone_exists()
    assert not default_shipping_zone_exists(shipping_zone.pk)


def test_get_available_countries(shipping_zone):
    assert get_available_countries(shipping_zone.pk) == set(COUNTRY_CHOICES)
    assert get_available_countries() == (
        set(COUNTRY_CHOICES) - currently_used_countries())


def test_currently_used_countries():
    zone_1 = ShippingZone.objects.create(name='Zone 1', countries=['PL'])
    zone_2 = ShippingZone.objects.create(name='Zone 2', countries=['DE'])
    result = currently_used_countries(zone_1.pk)
    assert list(result)[0][0] == 'DE'


def test_shipping_zone_form():
    zone_1 = ShippingZone.objects.create(name='Zone 1', countries=['PL'])
    zone_2 = ShippingZone.objects.create(name='Zone 2', countries=['DE'])
    form = ShippingZoneForm(
        instance=zone_1, data={
            'name': 'Zone 1',
            'countries': ['PL']})

    assert 'DE' not in [
        code for code, name in form.fields['countries'].choices]
    assert form.is_valid()

    form = ShippingZoneForm(
        instance=zone_1, data={
            'name': 'Zone 2',
            'countries': ['DE']})
    assert not form.is_valid()
    assert 'countries' in form.errors


def test_create_duplicated_default_shipping_zone_form(shipping_zone):
    default_zone = ShippingZone.objects.create(name='Zone', default=True)
    form = ShippingZoneForm(
        instance=shipping_zone,
        data={'name': 'Zone', 'default': True, 'countries': ['PL']})
    assert form.fields['countries'].required
    assert form.fields['default'].disabled
    assert form.is_valid()
    zone = form.save()
    assert not zone.default


def test_add_default_shipping_zone_form():
    form = ShippingZoneForm(
        data={'name': 'Zone', 'countries': ['PL'], 'default': True})
    assert form.is_valid()
    zone = form.save()
    assert zone.default
    assert not zone.countries


@pytest.mark.parametrize(
    'min_price, max_price, result',
    (
        (10, 20, True), (None, None, True), (None, 10, True), (0, None, True),
        (20, 20, False)))
def test_price_shipping_method_form(min_price, max_price, result):
    data = {
        'name': 'Name',
        'price': 10,
        'minimum_order_price': min_price,
        'maximum_order_price': max_price}
    form = PriceShippingMethodForm(data=data)
    assert form.is_valid() == result


@pytest.mark.parametrize(
    'min_weight, max_weight, result',
    (
        (10, 20, True), (None, None, True), (None, 10, True), (0, None, True),
        (20, 20, False)))
def test_weight_shipping_method_form(min_weight, max_weight, result):
    data = {
        'name': 'Name',
        'price': 10,
        'minimum_order_weight': min_weight,
        'maximum_order_weight': max_weight}
    form = WeightShippingMethodForm(data=data)
    assert form.is_valid() == result


def test_shipping_zone_list(admin_client, shipping_zone):
    url = reverse('dashboard:shipping-zone-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_shipping_zone_update_default_weight_unit(admin_client, site_settings):
    url = reverse('dashboard:shipping-zone-list')
    data = {'default_weight_unit': WeightUnits.POUND}
    response = admin_client.post(url, data=data)
    assert response.status_code == 302
    site_settings.refresh_from_db()
    assert site_settings.default_weight_unit == WeightUnits.POUND


def test_shipping_zone_add(admin_client):
    assert ShippingZone.objects.count() == 0
    url = reverse('dashboard:shipping-zone-add')
    data = {'name': 'Zium', 'countries': ['PL']}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 1


def test_shipping_zone_add_not_valid(admin_client):
    assert ShippingZone.objects.count() == 0
    url = reverse('dashboard:shipping-zone-add')
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 0


def test_shipping_zone_edit(admin_client, shipping_zone):
    assert ShippingZone.objects.count() == 1
    url = reverse(
        'dashboard:shipping-zone-update', kwargs={'pk': shipping_zone.pk})
    data = {'name': 'Flash', 'countries': ['PL']}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 1
    assert ShippingZone.objects.all()[0].name == 'Flash'


def test_shipping_zone_details(admin_client, shipping_zone):
    assert ShippingZone.objects.count() == 1
    url = reverse(
        'dashboard:shipping-zone-details', kwargs={'pk': shipping_zone.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200


def test_shipping_zone_delete(admin_client, shipping_zone):
    assert ShippingZone.objects.count() == 1
    url = reverse(
        'dashboard:shipping-zone-delete', kwargs={'pk': shipping_zone.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert ShippingZone.objects.count() == 0


def test_shipping_method_add(admin_client, shipping_zone):
    assert ShippingMethod.objects.count() == 1
    url = reverse(
        'dashboard:shipping-method-add',
        kwargs={
            'shipping_zone_pk': shipping_zone.pk,
            'type': 'price'})
    data = {
        'name': 'DHL',
        'price': '50',
        'shipping_zone': shipping_zone.pk,
        'type': ShippingMethodType.PRICE_BASED}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingMethod.objects.count() == 2


def test_shipping_method_add_not_valid(admin_client, shipping_zone):
    assert ShippingMethod.objects.count() == 1
    url = reverse(
        'dashboard:shipping-method-add',
        kwargs={
            'shipping_zone_pk': shipping_zone.pk,
            'type': 'price'})
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingMethod.objects.count() == 1


def test_shipping_method_edit(admin_client, shipping_zone):
    assert ShippingMethod.objects.count() == 1
    country = shipping_zone.shipping_methods.all()[0]
    assert country.price == Money(10, 'USD')
    url = reverse(
        'dashboard:shipping-method-edit',
        kwargs={
            'shipping_zone_pk': shipping_zone.pk,
            'shipping_method_pk': country.pk})
    data = {
        'name': 'DHL',
        'price': '50',
        'shipping_zone': shipping_zone.pk,
        'type': ShippingMethodType.PRICE_BASED}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert ShippingMethod.objects.count() == 1

    shipping_price = shipping_zone.shipping_methods.all()[0].price
    assert shipping_price == Money(50, 'USD')


def test_shipping_method_delete(admin_client, shipping_zone):
    assert ShippingMethod.objects.count() == 1
    country = shipping_zone.shipping_methods.all()[0]
    url = reverse(
        'dashboard:shipping-method-delete',
        kwargs={
            'shipping_zone_pk': shipping_zone.pk,
            'shipping_method_pk': country.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert ShippingMethod.objects.count() == 0
