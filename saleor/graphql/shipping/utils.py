from collections.abc import Iterable
from typing import Optional, overload

from django.core.exceptions import ValidationError

from ...shipping import models
from ..core.utils import from_global_id_or_error
from .types import ShippingMethod, ShippingMethodType


@overload
def get_shipping_model_by_object_id(
    object_id: str, raise_error=True, error_field="id"
) -> models.ShippingMethod: ...


@overload
def get_shipping_model_by_object_id(
    object_id: Optional[str], raise_error=False, error_field="id"
) -> Optional[models.ShippingMethod]: ...


def get_shipping_model_by_object_id(object_id, raise_error=True, error_field="id"):
    if object_id:
        type, object_pk = from_global_id_or_error(object_id)
        if type not in [str(ShippingMethod), str(ShippingMethodType)]:
            raise ValidationError(
                {
                    error_field: ValidationError(
                        "Must receive a ShippingMethod or ShippingMethodType id.",
                        code="invalid",
                    )
                }
            )
        shipping_method = models.ShippingMethod.objects.filter(pk=object_pk).first()
        if not shipping_method and raise_error:
            raise ValidationError(
                {
                    error_field: ValidationError(
                        f"Couldn't resolve to a node: {object_id}", code="not_found"
                    )
                }
            )
        return shipping_method
    return None


def get_instances_by_object_ids(
    object_ids: list[str],
) -> Iterable[models.ShippingMethod]:
    model_ids = []
    for object_id in object_ids:
        _, object_pk = from_global_id_or_error(object_id)
        model_ids.append(object_pk)
    return models.ShippingMethod.objects.filter(pk__in=model_ids)
