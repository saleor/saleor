import json
from typing import Iterable, Optional

import Adyen
from django.conf import settings
from django_countries.fields import Country
from promise import Promise

from ....checkout import calculations
from ....checkout.models import Checkout, CheckoutLine
from ....core.prices import quantize_price
from ....discount import DiscountInfo
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ... import PaymentError, TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData, PaymentGateway
from ..utils import get_supported_currencies

GATEWAY_NAME = "Adyen"


def require_active_plugin(fn):
    def wrapped(self, *args, **kwargs):
        previous = kwargs.get("previous_value", None)
        if not self.active:
            return previous
        return fn(self, *args, **kwargs)

    return wrapped


class AdyenGatewayPlugin(BasePlugin):

    PLUGIN_ID = "mirumee.payments.adyen"
    PLUGIN_NAME = GATEWAY_NAME
    DEFAULT_CONFIGURATION = [
        {"name": "Merchant Account", "value": None},
        {"name": "API key", "value": None},
        {"name": "Supported currencies", "value": ""},
        {"name": "Return Url", "value": ""},
        {"name": "Origin Key", "value": ""},
        {"name": "Origin Url", "value": ""},
    ]

    CONFIG_STRUCTURE = {
        "API key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "To submit payments to Adyen, you'll be making API requests that are "
                "authenticated with an API key. You can generate API keys on your "
                "Customer Area."
            ),
            "label": "API key",
        },
        "Merchant Account": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Yout merchant account name.",
            "label": "Merchant Account",
        },
        "Supported currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
        "Return Url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "",
            "label": "Return Url",
        },
        "Origin Key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "",
            "label": "Origin Key",
        },
        "Origin Url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "",
            "label": "Origin Url",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=True,  # FIXME check this
            supported_currencies=configuration["Supported currencies"],
            connection_params={
                "api_key": configuration["API key"],
                "merchant_account": configuration["Merchant Account"],
                "return_url": configuration["Return Url"],
                "origin_key": configuration["Origin Key"],
                "origin_url": configuration["Origin Url"],
            },
        )
        api_key = self.config.connection_params["api_key"]
        self.adyen = Adyen.Adyen(xapikey=api_key)

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    @require_active_plugin
    def get_payment_gateway_for_checkout(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLine"],
        discounts: Iterable["DiscountInfo"],
        previous_value,
    ) -> Optional["PaymentGateway"]:
        def checkout_total(data):
            lines, discounts = data
            return calculations.checkout_total(
                checkout=checkout, lines=lines, discounts=discounts
            )

        total = Promise.all([lines, discounts]).then(checkout_total)

        config = self._get_gateway_config()
        merchant_account = config.connection_params["merchant_account"]
        address = checkout.billing_address or checkout.shipping_address

        # FIXME check how it works if we have None here
        country = address.country if address else None
        if country:
            country_code = country.code
        else:
            country_code = Country(settings.DEFAULT_COUNTRY).code
        channel = checkout.get_value_from_metadata("channel", "web")
        checkout.get_total_gift_cards_balance()
        request = {
            "merchantAccount": merchant_account,
            "countryCode": country_code,
            # "shopperLocale":
            # "amount": {
            #     "value": float(
            #         quantize_price(total.get().gross.amount, checkout.currency)
            #     ),
            #     "currency": checkout.currency,
            # },
            "channel": channel,
        }
        response = self.adyen.checkout.payment_methods(request)
        # self.adyen.checkout.origin_keys()
        print(response.message)
        return PaymentGateway(
            id=self.PLUGIN_ID,
            name=self.PLUGIN_NAME,
            config=[
                {
                    "field": "origin_key",
                    "value": config.connection_params["origin_key"],
                },
                {
                    "field": "config",
                    "value": json.dumps(response.message["paymentMethods"]),
                },
            ],
            currencies=self.get_supported_currencies([]),
        )

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        extra_data = json.loads(payment_information.extra_data)  # try catch here
        print(extra_data)
        payment_data = extra_data.get("payment_data")
        # this is additional parameter which comes from
        if not payment_data.pop("is_valid", True):
            raise PaymentError("Payment data are not valid")

        extra_request_params = {}
        if "browserInfo" in payment_data:
            extra_request_params["browserInfo"] = payment_data["browserInfo"]
        if "billingAddress" in payment_data:
            extra_request_params["billingAddress"] = payment_data["billingAddress"]
        if "shopperIP" in payment_data:
            extra_request_params["shopperIP"] = payment_data["shopperIP"]
        if (
            "browserInfo" in extra_request_params
            and "billingAddress" in extra_request_params
        ):
            # Replace this assigment. Add note that customer_ip_address has incorrect name
            # Add to dashboard config the flow to combine channel with url like:
            # web1:https://shop.com, web2:https://shop1.com
            extra_request_params["origin"] = self.config.connection_params["origin_url"]

        result = self.adyen.checkout.payments(
            {
                "amount": {
                    "value": float(
                        quantize_price(
                            payment_information.amount, payment_information.currency
                        )
                    ),
                    "currency": payment_information.currency,
                },
                "reference": payment_information.payment_id,
                "paymentMethod": payment_data["paymentMethod"],
                "returnUrl": self.config.connection_params["return_url"],
                "merchantAccount": self.config.connection_params["merchant_account"],
                **extra_request_params,
            }
        )
        FAILED_STATUSES = ["refused", "error", "cancelled"]
        # Check if further action is needed
        # if 'action' in result.message:
        # Pass the action object to your front end
        # result.message['action']
        # else:
        # No further action needed, pass the resultCode to your front end
        # result.message['resultCode']
        # FIXME Assign token
        is_success = result.message["resultCode"].strip().lower() not in FAILED_STATUSES
        return GatewayResponse(
            is_success=is_success,
            action_required="action" in result.message,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=payment_data.get("pspReference", ""),
            error=None,  # FIXME
            raw_response=result.message,
        )

    @require_active_plugin
    def get_payment_config(self, previous_value):
        return []

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)
