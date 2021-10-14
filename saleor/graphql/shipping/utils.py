from ...plugins.base_plugin import ShippingMethod as ShippingMethodDataclass
from ...plugins.base_plugin import Weight
from ...shipping import models as shipping_models


def convert_shipping_method_model_to_dataclass(
    shipping_method: shipping_models.ShippingMethod,
):
    shipping_method_dataclass = ShippingMethodDataclass(
        id=str(shipping_method.id),
        price=shipping_method.price,  # type: ignore
        name=shipping_method.name,
        maximum_delivery_days=shipping_method.maximum_delivery_days,
        minimum_delivery_days=shipping_method.minimum_delivery_days,
        maximum_order_weight=None,
        minimum_order_weight=None,
    )
    if max_weight := shipping_method.maximum_order_weight:
        shipping_method_dataclass.maximum_order_weight = Weight(
            unit=max_weight.unit,
            value=max_weight.value,
        )

    if min_weight := shipping_method.maximum_order_weight:
        shipping_method_dataclass.minimum_order_weight = Weight(
            unit=min_weight.unit,
            value=min_weight.value,
        )
    return shipping_method_dataclass
