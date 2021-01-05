import json
from typing import List, Optional
from urllib.parse import urlencode

import Adyen
from django.contrib.auth.hashers import make_password
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound
from requests.exceptions import SSLError

from ....checkout.models import Checkout
from ....core.utils import build_absolute_uri
from ....core.utils.url import prepare_url
from ....order.events import external_notification_event
from ....plugins.base_plugin import BasePlugin, ConfigurationTypeField
from ....plugins.error_codes import PluginErrorCode
from ....plugins.models import PluginConfiguration
from ... import PaymentError, TransactionKind
from ...interface import (
    GatewayConfig,
    GatewayResponse,
    InitializedPaymentResponse,
    PaymentData,
    PaymentGateway,
)
from ...models import Payment, Transaction
from ..utils import get_supported_currencies
from .utils.apple_pay import initialize_apple_pay, make_request_to_initialize_apple_pay
from .utils.common import (
    AUTH_STATUS,
    FAILED_STATUSES,
    PENDING_STATUSES,
    api_call,
    call_capture,
    get_payment_method_info,
    request_data_for_gateway_config,
    request_data_for_payment,
    request_for_payment_cancel,
    request_for_payment_refund,
    update_payment_with_action_required_data,
)
from .webhooks import handle_additional_actions, handle_webhook

GATEWAY_NAME = "Adyen"
WEBHOOK_PATH = "/webhooks"
ADDITIONAL_ACTION_PATH = "/additional-actions"


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
        {"name": "merchant-account", "value": None},
        {"name": "api-key", "value": None},
        {"name": "supported-currencies", "value": ""},
        {"name": "client-key", "value": ""},
        {"name": "live", "value": ""},
        {"name": "adyen-auto-capture", "value": True},
        {"name": "auto-capture", "value": False},
        {"name": "hmac-secret-key", "value": ""},
        {"name": "notification-user", "value": ""},
        {"name": "notification-password", "value": ""},
        {"name": "enable-native-3d-secure", "value": False},
        {"name": "apple-pay-cert", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "api-key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "To submit payments to Adyen, you'll be making API requests that are "
                "authenticated with an API key. You can generate API keys on your "
                "Customer Area."
            ),
            "label": "API key",
        },
        "merchant-account": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Yout merchant account name.",
            "label": "Merchant Account",
        },
        "supported-currencies": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Determines currencies supported by gateway."
            " Please enter currency codes separated by a comma.",
            "label": "Supported currencies",
        },
        "client-key": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The client key is a public key that uniquely identifies a web service "
                "user. Each web service user has a list of allowed origins, or domains "
                "from which we expect to get your requests. We make sure data cannot "
                "be accessed by unknown parties by using Cross-Origin Resource Sharing."
                "Not required for Android or iOS app."
            ),
            "label": "Client Key",
        },
        "live": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Leave it blank when you want to use test env. To communicate with the"
                " Adyen API you should submit HTTP POST requests to corresponding "
                "endpoints. These endpoints differ for test and live accounts, and also"
                " depend on the data format (SOAP, JSON, or FORM) you use to submit "
                "data to the Adyen payments platform. "
                "https://docs.adyen.com/development-resources/live-endpoints"
            ),
            "label": "Live",
        },
        "adyen-auto-capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "All authorized payments will be marked as captured. This should only"
                " be enabled if Adyen is configured to auto-capture payments."
                " Saleor doesn't support the delayed capture Adyen feature."
            ),
            "label": "Assume all authorizations are automatically captured by Adyen",
        },
        "auto-capture": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "If enabled, Saleor will automatically capture funds. If, disabled, the"
                " funds are blocked but need to be captured manually."
            ),
            "label": "Automatically capture funds when a payment is made",
        },
        "hmac-secret-key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "Provide secret key generated on Adyen side."
                "https://docs.adyen.com/development-resources/webhooks#set-up-notificat"
                "ions-in-your-customer-area. The Saleor webhook url is "
                "http(s)://<your-backend-url>/plugins/mirumee.payments.adyen/webhooks/"
            ),
            "label": "HMAC secret key",
        },
        "notification-user": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Base User provided on the Adyen side to authenticate incoming "
                "notifications. https://docs.adyen.com/development-resources/webhooks#"
                "set-up-notifications-in-your-customer-area "
                "The Saleor webhook url is "
                "http(s)://<your-backend-url>/plugins/mirumee.payments.adyen/webhooks/"
            ),
            "label": "Notification user",
        },
        "notification-password": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "User password provided on the Adyen side for authenticate incoming "
                "notifications. https://docs.adyen.com/development-resources/webhooks#"
                "set-up-notifications-in-your-customer-area "
                "The Saleor webhook url is "
                "http(s)://<your-backend-url>/plugins/mirumee.payments.adyen/webhooks/"
            ),
            "label": "Notification password",
        },
        "enable-native-3d-secure": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Saleor uses 3D Secure redirect authentication by default. If you want"
                " to use native 3D Secure authentication, enable this option. For more"
                " details see Adyen documentation: native - "
                "https://docs.adyen.com/checkout/3d-secure/native-3ds2, redirect"
                " - https://docs.adyen.com/checkout/3d-secure/redirect-3ds2-3ds1"
            ),
            "label": "Enable native 3D Secure",
        },
        "apple-pay-cert": {
            "type": ConfigurationTypeField.SECRET_MULTILINE,
            "help_text": (
                "Follow the Adyen docs related to activating the Apple Pay for the "
                "web - https://docs.adyen.com/payment-methods/apple-pay/"
                "enable-apple-pay. This certificate is only required when you offer "
                "the Apple Pay as a web payment method.  Leave it blank if you don't "
                "offer Apple Pay or offer it only as a payment method in your iOS app."
            ),
            "label": "Apple Pay certificate",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=configuration["auto-capture"],
            supported_currencies=configuration["supported-currencies"],
            connection_params={
                "api_key": configuration["api-key"],
                "merchant_account": configuration["merchant-account"],
                "client_key": configuration["client-key"],
                "live": configuration["live"],
                "webhook_hmac": configuration["hmac-secret-key"],
                "webhook_user": configuration["notification-user"],
                "webhook_user_password": configuration["notification-password"],
                "adyen_auto_capture": configuration["adyen-auto-capture"],
                "enable_native_3d_secure": configuration["enable-native-3d-secure"],
                "apple_pay_cert": configuration["apple-pay-cert"],
            },
        )
        api_key = self.config.connection_params["api_key"]

        live_endpoint = self.config.connection_params["live"] or None
        platform = "live" if live_endpoint else "test"
        self.adyen = Adyen.Adyen(
            xapikey=api_key, live_endpoint_prefix=live_endpoint, platform=platform
        )

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        config = self._get_gateway_config()
        if path.startswith(WEBHOOK_PATH):
            return handle_webhook(request, config)
        elif path.startswith(ADDITIONAL_ACTION_PATH):
            return handle_additional_actions(
                request,
                self.adyen.checkout.payments_details,
            )
        return HttpResponseNotFound()

    def _get_gateway_config(self) -> GatewayConfig:
        return self.config

    @require_active_plugin
    def token_is_required_as_payment_input(self, previous_value):
        return False

    @require_active_plugin
    def initialize_payment(
        self, payment_data, previous_value
    ) -> "InitializedPaymentResponse":
        payment_method = payment_data.get("paymentMethod")
        if payment_method == "applepay":
            # The apple pay on the web requires additional step
            session_obj = initialize_apple_pay(
                payment_data, self.config.connection_params["apple_pay_cert"]
            )
            return InitializedPaymentResponse(
                gateway=self.PLUGIN_ID, name=self.PLUGIN_NAME, data=session_obj
            )
        return previous_value

    @require_active_plugin
    def get_payment_gateway_for_checkout(
        self,
        checkout: "Checkout",
        previous_value,
    ) -> Optional["PaymentGateway"]:

        config = self._get_gateway_config()
        request = request_data_for_gateway_config(
            checkout, config.connection_params["merchant_account"]
        )
        response = api_call(request, self.adyen.checkout.payment_methods)
        return PaymentGateway(
            id=self.PLUGIN_ID,
            name=self.PLUGIN_NAME,
            config=[
                {
                    "field": "client_key",
                    "value": config.connection_params["client_key"],
                },
                {"field": "config", "value": json.dumps(response.message)},
            ],
            currencies=self.get_supported_currencies([]),
        )

    @property
    def order_auto_confirmation(self):
        site_settings = Site.objects.get_current().settings
        return site_settings.automatically_confirm_all_new_orders

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        try:
            payment = Payment.objects.get(pk=payment_information.payment_id)
        except ObjectDoesNotExist:
            raise PaymentError("Payment cannot be performed. Payment does not exists.")

        checkout = payment.checkout
        if checkout is None:
            raise PaymentError(
                "Payment cannot be performed. Checkout for this payment does not exist."
            )

        params = urlencode(
            {"payment": payment_information.graphql_payment_id, "checkout": checkout.pk}
        )
        return_url = prepare_url(
            params,
            build_absolute_uri(
                f"/plugins/{self.PLUGIN_ID}/additional-actions"
            ),  # type: ignore
        )
        request_data = request_data_for_payment(
            payment_information,
            return_url=return_url,
            merchant_account=self.config.connection_params["merchant_account"],
            native_3d_secure=self.config.connection_params["enable_native_3d_secure"],
        )
        result = api_call(request_data, self.adyen.checkout.payments)
        result_code = result.message["resultCode"].strip().lower()
        is_success = result_code not in FAILED_STATUSES
        adyen_auto_capture = self.config.connection_params["adyen_auto_capture"]
        kind = TransactionKind.AUTH
        if result_code in PENDING_STATUSES:
            kind = TransactionKind.PENDING
        elif adyen_auto_capture:
            kind = TransactionKind.CAPTURE
        searchable_key = result.message.get("pspReference", "")
        action = result.message.get("action")
        error_message = result.message.get("refusalReason")
        if action:
            update_payment_with_action_required_data(
                payment,
                action,
                result.message.get("details", []),
            )
        # If auto capture is enabled, let's make a capture the auth payment
        elif (
            self.config.auto_capture
            and result_code == AUTH_STATUS
            and self.order_auto_confirmation
        ):
            kind = TransactionKind.CAPTURE
            result = call_capture(
                payment_information=payment_information,
                merchant_account=self.config.connection_params["merchant_account"],
                token=result.message.get("pspReference"),
                adyen_client=self.adyen,
            )
        payment_method_info = get_payment_method_info(payment_information, result)
        return GatewayResponse(
            is_success=is_success,
            action_required="action" in result.message,
            kind=kind,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=result.message.get("pspReference", ""),
            error=error_message,
            raw_response=result.message,
            action_required_data=action,
            payment_method_info=payment_method_info,
            searchable_key=searchable_key,
        )

    @classmethod
    def _update_config_items(
        cls, configuration_to_update: List[dict], current_config: List[dict]
    ):
        for item in configuration_to_update:
            if item.get("name") == "notification-password" and item["value"]:
                item["value"] = make_password(item["value"])
        super()._update_config_items(configuration_to_update, current_config)

    @require_active_plugin
    def get_payment_config(self, previous_value):
        return []

    @require_active_plugin
    def get_supported_currencies(self, previous_value):
        config = self._get_gateway_config()
        return get_supported_currencies(config, GATEWAY_NAME)

    def _process_additional_action(self, payment_information: "PaymentData", kind: str):
        config = self._get_gateway_config()
        additional_data = payment_information.data
        if not additional_data:
            raise PaymentError("Unable to finish the payment.")

        result = api_call(additional_data, self.adyen.checkout.payments_details)
        result_code = result.message["resultCode"].strip().lower()
        is_success = result_code not in FAILED_STATUSES
        action_required = "action" in result.message
        if result_code in PENDING_STATUSES:
            kind = TransactionKind.PENDING
        elif (
            is_success
            and config.auto_capture
            and self.order_auto_confirmation
            and not action_required
        ):
            # For enabled auto_capture on Saleor side we need to proceed an additional
            # action
            kind = TransactionKind.CAPTURE
            result = call_capture(
                payment_information=payment_information,
                merchant_account=self.config.connection_params["merchant_account"],
                token=result.message.get("pspReference"),
                adyen_client=self.adyen,
            )

        payment_method_info = get_payment_method_info(payment_information, result)
        action = result.message.get("action")
        return GatewayResponse(
            is_success=is_success,
            action_required=action_required,
            action_required_data=action,
            kind=kind,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=result.message.get("pspReference", ""),
            error=result.message.get("refusalReason"),
            raw_response=result.message,
            searchable_key=result.message.get("pspReference", ""),
            payment_method_info=payment_method_info,
        )

    @require_active_plugin
    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        config = self._get_gateway_config()
        # The additional checks are proceed asynchronously so we try to confirm that
        # the payment is already processed
        payment = Payment.objects.filter(id=payment_information.payment_id).first()
        if not payment:
            raise PaymentError("Unable to find the payment.")

        transaction = (
            payment.transactions.filter(
                kind=TransactionKind.ACTION_TO_CONFIRM,
                is_success=True,
                action_required=False,
            )
            .exclude(token__isnull=False, token__exact="")
            .last()
        )

        adyen_auto_capture = self.config.connection_params["adyen_auto_capture"]
        kind = TransactionKind.AUTH
        if adyen_auto_capture or config.auto_capture:
            kind = TransactionKind.CAPTURE

        if not transaction:
            # We don't have async notification for this payment so we try to proceed
            # standard flow for confirming an additional action
            return self._process_additional_action(payment_information, kind)

        result_code = transaction.gateway_response.get("resultCode", "").strip().lower()
        if result_code and result_code in PENDING_STATUSES:
            kind = TransactionKind.PENDING

        # We already have the ACTION_TO_CONFIRM transaction, it means that
        # payment was processed asynchronous and no additional action is required

        # Check if we didn't process this transaction asynchronously
        transaction_already_processed = payment.transactions.filter(
            kind=kind,
            is_success=True,
            action_required=False,
            amount=payment_information.amount,
            currency=payment_information.currency,
        ).first()
        is_success = True

        # confirm that we should proceed the capture action
        if (
            not transaction_already_processed
            and config.auto_capture
            and kind == TransactionKind.CAPTURE
        ):
            response = self.capture_payment(payment_information, None)
            is_success = response.is_success

        token = transaction.token
        if transaction_already_processed:
            token = transaction_already_processed.token

        return GatewayResponse(
            is_success=is_success,
            action_required=False,
            kind=kind,
            amount=payment_information.amount,  # type: ignore
            currency=payment_information.currency,  # type: ignore
            transaction_id=token,  # type: ignore
            error=None,
            raw_response={},
            transaction_already_processed=bool(transaction_already_processed),
        )

    @require_active_plugin
    def refund_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        # we take Auth kind because it contains the transaction id that we need
        transaction = (
            Transaction.objects.filter(
                payment__id=payment_information.payment_id,
                kind=TransactionKind.AUTH,
                is_success=True,
            )
            .exclude(token__isnull=False, token__exact="")
            .last()
        )

        if not transaction:
            # If we don't find the Auth kind we will try to get Capture kind
            transaction = (
                Transaction.objects.filter(
                    payment__id=payment_information.payment_id,
                    kind=TransactionKind.CAPTURE,
                    is_success=True,
                )
                .exclude(token__isnull=False, token__exact="")
                .last()
            )

        if not transaction:
            raise PaymentError("Cannot find a payment reference to refund.")

        request = request_for_payment_refund(
            payment_information=payment_information,
            merchant_account=self.config.connection_params["merchant_account"],
            token=transaction.token,
        )
        result = api_call(request, self.adyen.payment.refund)

        amount = payment_information.amount
        currency = payment_information.currency
        if transaction.payment.order:
            msg = f"Adyen: Refund for amount {amount}{currency} has been requested."
            external_notification_event(
                order=transaction.payment.order,  # type: ignore
                user=None,
                message=msg,
                parameters={
                    "service": transaction.payment.gateway,
                    "id": transaction.payment.token,
                },
            )
        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind=TransactionKind.REFUND_ONGOING,
            amount=amount,
            currency=currency,
            transaction_id=result.message.get("pspReference", ""),
            error="",
            raw_response=result.message,
            searchable_key=result.message.get("pspReference", ""),
        )

    @require_active_plugin
    def capture_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":

        if not payment_information.token:
            raise PaymentError("Cannot find a payment reference to capture.")

        result = call_capture(
            payment_information=payment_information,
            merchant_account=self.config.connection_params["merchant_account"],
            token=payment_information.token,
            adyen_client=self.adyen,
        )

        payment_method_info = get_payment_method_info(payment_information, result)

        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind=TransactionKind.CAPTURE,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=result.message.get("pspReference", ""),
            error="",
            raw_response=result.message,
            payment_method_info=payment_method_info,
            searchable_key=result.message.get("pspReference", ""),
        )

    @require_active_plugin
    def void_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        request = request_for_payment_cancel(
            payment_information=payment_information,
            merchant_account=self.config.connection_params["merchant_account"],
            token=payment_information.token,  # type: ignore
        )
        result = api_call(request, self.adyen.payment.cancel)

        return GatewayResponse(
            is_success=True,
            action_required=False,
            kind=TransactionKind.VOID,
            amount=payment_information.amount,
            currency=payment_information.currency,
            transaction_id=result.message.get("pspReference", ""),
            error="",
            raw_response=result.message,
            searchable_key=result.message.get("pspReference", ""),
        )

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        apple_certificate = configuration.get("apple-pay-cert")
        if plugin_configuration.active and apple_certificate:
            global_apple_url = (
                "https://apple-pay-gateway.apple.com/paymentservices/paymentSession"
            )
            request_data = {
                "merchantIdentifier": "",
                "displayName": "",
                "initiative": "web",
                "initiativeContext": "",
            }
            # Try to exectue the session request without all required data. If the
            # apple certificate is correct we will get the error related to the missing
            # parameters. If certificate is incorrect, the SSL error will be raised.
            try:
                make_request_to_initialize_apple_pay(
                    validation_url=global_apple_url,
                    request_data=request_data,
                    certificate=apple_certificate,
                )
            except SSLError:
                raise ValidationError(
                    {
                        "apple-pay-cert": ValidationError(
                            "The provided apple certificate is invalid.",
                            code=PluginErrorCode.INVALID.value,
                        )
                    }
                )
            except Exception:
                pass
