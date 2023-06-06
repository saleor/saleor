from typing import Union

from django.core.management.base import BaseCommand
from pydantic import schema_json_of

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


class Command(BaseCommand):
    help = "Writes selected JSON-schema to stdout"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            schema_json_of(
                Union[
                    Manifest,
                    CheckoutCalculateTaxes,
                    OrderCalculateTaxes,
                    ShippingListMethodsForCheckout,
                ],
                title="Schema",
                indent=2,
            )
        )
