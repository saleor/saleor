import json
from typing import Type

from django.core.management.base import BaseCommand
from pydantic import BaseModel
from pydantic.schema import schema

from ....app.manifest_schema import Manifest
from ....plugins.webhook.shipping import ShippingMethodsSchema
from ...taxes import TaxData


class CheckoutCalculateTaxes(TaxData):
    class Config:
        title = "CHECKOUT_CALCULATE_TAXES"


class OrderCalculateTaxes(TaxData):
    class Config:
        title = "ORDER_CALCULATE_TAXES"


class ShippingListMethodsForCheckout(ShippingMethodsSchema):
    class Config:
        title = "SHIPPING_LIST_METHODS_FOR_CHECKOUT"


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
