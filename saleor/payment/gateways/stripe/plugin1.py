import json
from typing import TYPE_CHECKING, List, Tuple

import stripe
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from stripe.error import StripeError
from stripe.stripe_object import StripeObject

from .stripe_api import retrieve_webhook, subscribe_to_webhook, is_secret_api_key_valid, \
    create_payment_intent, retrieve_payment_intent
from .webhooks import handle_webhook
from ... import TransactionKind
from ...models import Payment, Transaction
from ...utils import price_to_minor_unit, price_from_minor_unit
from ....graphql.core.enums import PluginErrorCode
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField

from ..utils import get_supported_currencies, require_active_plugin
from . import (
    GatewayConfig,
)

GATEWAY_NAME = "Stripe"

if TYPE_CHECKING:
    # flake8: noqa
    from ...interface import CustomerSource
    from ....plugins.models import PluginConfiguration
from . import GatewayResponse, PaymentData
from .consts import PLUGIN_NAME, PLUGIN_ID, WEBHOOK_PATH, ACTION_REQUIRED_STATUSES, \
    PROCESSING_STATUS, SUCCESS_STATUSES


class StripeGatewayPlugin(BasePlugin):
    PLUGIN_NAME = PLUGIN_NAME
    PLUGIN_ID = PLUGIN_ID
    DEFAULT_CONFIGURATION = [
        {"name": "public_api_key", "value": None},
        {"name": "secret_api_key", "value": None},
        {"name": "store_customers_cards", "value": False},
        {"name": "automatic_payment_capture", "value": True},
        {"name": "supported_currencies", "value": ""},
        {"name": "webhook_endpoint_id", "value": None},
        {"name": "webhook_secret_key", "value": None}
    ]

    CONFIG_STRUCTURE = {
        "public_api_key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide Stripe public API key.",
            "label": "Public API key",
        },
        "secret_api_key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Provide Stripe secret API key.",
            "label": "Secret API key",
        },
        "store_customers_cards": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should store cards on payments "
            "in Stripe customer.",
            "label": "Store customers card",
        },
        "automatic_payment_capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should automaticaly capture payments.",
            "label": "Automatic payment capture",
        },
        "supported_currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
    }

    def __init__(self, *args, **kwargs):

        # Webhook details are not listed in CONFIG_STRUCTURE as user input is not
        # required here
        plugin_configuration = kwargs.get("configuration")
        raw_configuration = {item["name"]: item["value"] for item in plugin_configuration}
        webhook_endpoint_id = raw_configuration.get("webhook_endpoint_id")
        webhook_secret = raw_configuration.get("webhook_secret_key")

        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["automatic_payment_capture"],
            supported_currencies=configuration["supported_currencies"],
            connection_params={
                "public_api_key": configuration["public_api_key"],
                "secret_api_key": configuration["secret_api_key"],
                "webhook_id": webhook_endpoint_id,
                "webhook_secret": webhook_secret
            },
            store_customer= False #configuration["Store customers card"],
        )

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        config = self.config
        if path.startswith(WEBHOOK_PATH, 1): # 1 as we don't check the '/'
            return handle_webhook(request, config)
        # return handle_webhook(request, config)

    @require_active_plugin
    def token_is_required_as_payment_input(self, previous_value):
        return False

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        return get_supported_currencies(self.config, GATEWAY_NAME)

    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":

        intent, error = create_payment_intent(
            api_key=self.config.connection_params["secret_api_key"],
            amount=payment_information.amount,
            currency=payment_information.currency
        )
        return GatewayResponse(
            is_success=True if not error else False,
            action_required=True,
            kind=TransactionKind.ACTION_TO_CONFIRM,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=intent.id if intent else "",
            error=error,
            raw_response=intent.last_response.data,
            action_required_data={"client_secret": intent.client_secret}
        )

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        payment_intent_id = payment_information.token
        api_key = self.config.connection_params["secret_api_key"]

        # before we will call stripe API, let's check if the transaction object hasn't
        # been created by webhook handler
        payment_transaction = Transaction.objects.filter(
            payment_id=payment_information.payment_id,
            is_success=True,
            action_required=False,
            kind__in=[TransactionKind.AUTH, TransactionKind.CAPTURE]
        ).first()

        if payment_transaction:
            return GatewayResponse(
                is_success=True,
                action_required=False,
                kind=payment_transaction.kind,
                amount=payment_transaction.amount,
                currency=payment_transaction.currency,
                transaction_id=payment_transaction.token,
                error=None,
                raw_response=payment_transaction.gateway_response,
                transaction_already_processed=True
            )

        payment_intent = retrieve_payment_intent(api_key, payment_intent_id)
        kind = TransactionKind.CAPTURE if self.config.auto_capture else TransactionKind.AUTH
        action_required = False

        if payment_intent:
            amount = price_from_minor_unit(payment_intent.amount,
                                           payment_intent.currency)
            currency = payment_intent.currency

            # payment still requires an action
            if payment_intent.status in ACTION_REQUIRED_STATUSES:
                kind = TransactionKind.ACTION_TO_CONFIRM
                action_required = True

            elif payment_intent.status == PROCESSING_STATUS:
                kind = TransactionKind.PENDING
            elif payment_intent.status == SUCCESS_STATUSES:
                kind = TransactionKind.CAPTURE if payment_intent.capture_method == "automatic" else TransactionKind.AUTH
        else:
            amount = payment_information.amount
            currency = payment_information.currency

        return GatewayResponse(
            is_success=True if payment_intent else False,
            action_required=action_required,
            kind=kind,
            amount=amount,
            currency=currency,
            transaction_id=payment_intent.id if payment_intent else "",
            error=None,
            raw_response=payment_intent.last_response.data if payment_intent else None,
        )


    @classmethod
    def pre_save_for_existing_webhook_configuration(
            cls,api_key, plugin_configuration:"PluginConfiguration", configuration:dict)->Tuple[StripeObject, bool]:
        # make sure that webhook exsits on Stripe side
        webhook = retrieve_webhook(api_key, configuration["webhook_endpoint_id"])

        new_subscription = False

        # remove the old webhook detail values if we were not able to fetch a
        # webhook with the id
        if not webhook:
            plugin_configuration.configuration.remove(
                {"name": "webhook_endpoint_id",
                 "value": configuration['webhook_endpoint_id']}
            )
            plugin_configuration.configuration.remove(
                {"name": "webhook_secret_key",
                 "value": configuration['webhook_secret_key']}
            )
            webhook = subscribe_to_webhook(api_key)
            new_subscription = True
        return webhook, new_subscription

    @classmethod
    def pre_save_for_non_existing_webhook_configuration(
            cls, api_key, plugin_configuration:"PluginConfiguration", configuration:dict)->StripeObject:
        # Create new webhook subscription in case when we don't have all webhook
        # details
        webhook = subscribe_to_webhook(api_key)
        if configuration.get('webhook_endpoint_id'):
            plugin_configuration.configuration.remove(
                {"name": "webhook_endpoint_id",
                 "value": configuration['webhook_endpoint_id']}
            )
        if configuration.get('webhook_secret_key'):
            plugin_configuration.configuration.remove(
                {"name": "webhook_secret_key",
                 "value": configuration['webhook_secret_key']}
            )
        return webhook

    @classmethod
    def pre_save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not plugin_configuration.active:
            return

        api_key = configuration['secret_api_key']
        # TODO call webhook subscription only when domain is not a localhost
        # print warning with localhost
        webhook_id = configuration.get("webhook_endpoint_id")
        webhook_secret = configuration.get("webhook_secret_key")
        if webhook_id and webhook_secret:
            webhook, new_subscription = cls.pre_save_for_existing_webhook_configuration(
                api_key,
                plugin_configuration,
                configuration
            )
        else:
            webhook = cls.pre_save_for_non_existing_webhook_configuration(
                api_key,
                plugin_configuration,
                configuration
            )
            new_subscription = True

        if new_subscription:
            plugin_configuration.configuration.extend([
                {
                    "name": "webhook_endpoint_id", "value": webhook.id
                },
                {
                    "name": "webhook_secret_key", "value": webhook.secret
                },
            ]
            )


    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        required_fields = [
            "secret_api_key",
            "public_api_key"
        ]
        all_required_fields_provided = all([configuration.get(field) for field in required_fields])
        if plugin_configuration.active:
            if not all_required_fields_provided:
                raise ValidationError(
                    {
                        field: ValidationError(
                            "The parameter is required.",
                            code=PluginErrorCode.REQUIRED.value
                        )

                    } for field in required_fields
                )

            api_key = configuration['secret_api_key']
            if not is_secret_api_key_valid(api_key):
                raise ValidationError(
                    {
                        "secret_api_key": ValidationError(
                            "Secret API key is incorrect.",
                            code=PluginErrorCode.INVALID.value
                        )
                    }
                )
