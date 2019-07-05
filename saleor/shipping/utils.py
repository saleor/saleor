from typing import TYPE_CHECKING, Union

from .models import ShippingMethod

if TYPE_CHECKING:
    from ..checkout.models import Checkout  # noqa: F401
    from ..order.models import Order  # noqa: F401


def applicable_shipping_methods(
    instance: Union["Checkout", "Order"], price, country_code=None
):
    if not instance.is_shipping_required():
        return None
    if not instance.shipping_address:
        return None

    qs = ShippingMethod.objects
    return qs.applicable_shipping_methods(
        price=price,
        weight=instance.get_total_weight(),
        country_code=country_code or instance.shipping_address.country.code,
    )
