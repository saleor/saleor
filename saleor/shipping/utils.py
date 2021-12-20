from typing import TYPE_CHECKING, Optional

from django_countries import countries

from .interface import ShippingMethodData

if TYPE_CHECKING:
    from .models import ShippingMethod


def default_shipping_zone_exists(zone_pk=None):
    from .models import ShippingZone

    return ShippingZone.objects.exclude(pk=zone_pk).filter(default=True)


def get_countries_without_shipping_zone():
    """Return countries that are not assigned to any shipping zone."""
    from .models import ShippingZone

    covered_countries = set()
    for zone in ShippingZone.objects.all():
        covered_countries.update({c.code for c in zone.countries})
    return (country[0] for country in countries if country[0] not in covered_countries)


def convert_to_shipping_method_data(
    shipping_method: Optional["ShippingMethod"],
) -> Optional["ShippingMethodData"]:
    if not shipping_method:
        return None

    return ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        price=getattr(shipping_method, "price", None),
        description=shipping_method.description,
        type=shipping_method.type,
        excluded_products=shipping_method.excluded_products,
        channel_listings=shipping_method.channel_listings,
        minimum_order_weight=shipping_method.minimum_order_weight,
        maximum_order_weight=shipping_method.maximum_order_weight,
        maximum_delivery_days=shipping_method.maximum_delivery_days,
        minimum_delivery_days=shipping_method.minimum_delivery_days,
        metadata=shipping_method.metadata,
        private_metadata=shipping_method.private_metadata,
    )
