import json
from typing import Type

from django.core.management.base import BaseCommand
from pydantic import BaseModel
from pydantic.schema import schema

from ....app.manifest_schema import Manifest
from ....graphql.core.descriptions import ADDED_IN_36, ADDED_IN_37
from ....plugins.webhook.shipping import ShippingMethodsSchema
from ...taxes import TaxData


class CheckoutCalculateTaxes(TaxData):
    """Response from webhook with calculated checkout taxes."""

    class Config:
        title = "CHECKOUT_CALCULATE_TAXES"


CheckoutCalculateTaxes.__doc__ += ADDED_IN_37


class OrderCalculateTaxes(TaxData):
    """Response from webhook with calculated order taxes."""

    class Config:
        title = "ORDER_CALCULATE_TAXES"


OrderCalculateTaxes.__doc__ += ADDED_IN_37


class ShippingListMethodsForCheckout(ShippingMethodsSchema):
    """Response from webhook with shipping methods that can be used with checkout."""

    class Config:
        title = "SHIPPING_LIST_METHODS_FOR_CHECKOUT"


ShippingListMethodsForCheckout.__doc__ += ADDED_IN_36

SCHEMA: list[Type[BaseModel]] = [
    Manifest,
    CheckoutCalculateTaxes,
    OrderCalculateTaxes,
    ShippingListMethodsForCheckout,
]


class Command(BaseCommand):
    help = "Writes selected JSON-schema to stdout"

    def handle(self, *args, **kwargs):
        top_level_schema = {"$schema": "http://json-schema.org/draft-07/schema#"}
        top_level_schema.update(schema(SCHEMA))
        self.stdout.write(json.dumps(top_level_schema, indent=2))
