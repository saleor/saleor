import json
import logging
from typing import Any

from pydantic import ValidationError

from ...app.models import App
from ...shipping.interface import ShippingMethodData
from ..response_schemas.shipping import (
    ListShippingMethodsSchema,
)

logger = logging.getLogger(__name__)


def parse_list_shipping_methods_response(
    response_data: Any, app: "App", object_currency: str
) -> list["ShippingMethodData"]:
    try:
        list_shipping_method_model = ListShippingMethodsSchema.model_validate(
            response_data,
            context={
                "app": app,
                "currency": object_currency,
                "custom_message": "Skipping invalid shipping method (ListShippingMethodsSchema)",
            },
        )
    except ValidationError:
        logger.warning("Skipping invalid shipping method response: %s", response_data)
        return []
    return [
        ShippingMethodData(
            id=shipping_method.id,
            name=shipping_method.name,
            price=shipping_method.price,
            maximum_delivery_days=shipping_method.maximum_delivery_days,
            minimum_delivery_days=shipping_method.minimum_delivery_days,
            description=shipping_method.description,
            metadata=shipping_method.metadata,
            private_metadata=shipping_method.private_metadata,
        )
        for shipping_method in list_shipping_method_model.root
    ]


def get_cache_data_for_shipping_list_methods_for_checkout(payload: str) -> dict:
    key_data = json.loads(payload)

    # drop fields that change between requests but are not relevant for cache key
    key_data[0].pop("last_change")
    key_data[0].pop("meta")
    # Drop the external_app_shipping_id from the cache key as it should not have an
    # impact on cache invalidation
    if "external_app_shipping_id" in key_data[0].get("private_metadata", {}):
        del key_data[0]["private_metadata"]["external_app_shipping_id"]
    return key_data
