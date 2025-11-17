import logging
from typing import TYPE_CHECKING, Optional

from django_countries import countries

from ..core.db.connection import allow_writer
from ..plugins.base_plugin import ExcludedShippingMethod
from .interface import ShippingMethodData

if TYPE_CHECKING:
    from ..tax.models import TaxClass
    from .models import ShippingMethod, ShippingMethodChannelListing


logger = logging.getLogger(__name__)


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
    shipping_method: "ShippingMethod",
    listing: "ShippingMethodChannelListing",
    tax_class: Optional["TaxClass"] = None,
) -> "ShippingMethodData":
    price = listing.price
    minimum_order_price = listing.minimum_order_price
    maximum_order_price = listing.maximum_order_price

    if not tax_class:
        # Tax class should be passed as argument, this is a fallback.
        # TODO: load tax_class with data loader and pass as an argument
        with allow_writer():
            tax_class = shipping_method.tax_class

    return ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        description=shipping_method.description,
        type=shipping_method.type,
        minimum_order_weight=shipping_method.minimum_order_weight,
        maximum_order_weight=shipping_method.maximum_order_weight,
        maximum_delivery_days=shipping_method.maximum_delivery_days,
        minimum_delivery_days=shipping_method.minimum_delivery_days,
        metadata=shipping_method.metadata,
        private_metadata=shipping_method.private_metadata,
        price=price,
        tax_class=tax_class,
        minimum_order_price=minimum_order_price,
        maximum_order_price=maximum_order_price,
    )


def initialize_shipping_method_active_status(
    shipping_methods: list["ShippingMethodData"],
    excluded_methods: list["ExcludedShippingMethod"],
):
    reason_map = {str(method.id): method.reason for method in excluded_methods}
    for instance in shipping_methods:
        instance.active = True
        instance.message = ""
        reason = reason_map.get(str(instance.id))
        if reason is not None:
            instance.active = False
            instance.message = reason
