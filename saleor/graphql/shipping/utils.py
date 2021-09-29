from typing import Optional

from ...shipping.models import ShippingMethod
from ..core.utils import from_global_id_or_error


def get_shipping_model_by_object_id(object_id: Optional[str]) -> Optional[ShippingMethod]:
    if object_id:
        _, object_pk = from_global_id_or_error(object_id)
        shipping_method = ShippingMethod.objects.filter(pk=object_pk).first()
        return ShippingMethod.objects.filter(pk=object_pk).first()
    return None
