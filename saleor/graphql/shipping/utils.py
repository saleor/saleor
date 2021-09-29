from typing import List, Optional

from ...shipping.models import ShippingMethod
from ..core.utils import from_global_id_or_error


def get_shipping_model_by_object_id(
    object_id: Optional[str],
) -> Optional[ShippingMethod]:
    if object_id:
        _, object_pk = from_global_id_or_error(object_id)
        return ShippingMethod.objects.filter(pk=object_pk).first()
    return None


def get_instances_by_object_ids(object_ids: List[str]) -> List[ShippingMethod]:
    model_ids = []
    for object_id in object_ids:
        _, object_pk = from_global_id_or_error(object_id)
        model_ids.append(object_pk)
    return ShippingMethod.objects.filter(pk__in=model_ids)
