from prices import Price
import pytest

from django.conf import settings

from .models import ShippingMethod, ShippingMethodCountry


@pytest.fixture
def shipping_method(db):
    shipping_method = ShippingMethod.objects.create(name='Shipping method')
    shipping_method_country = ShippingMethodCountry.objects.create(
        country_code='PL', shipping_method=shipping_method,
        price=Price('3.0', currency=settings.DEFAULT_CURRENCY))
    return shipping_method_country
