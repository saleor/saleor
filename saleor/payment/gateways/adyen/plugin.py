import json
from typing import List, Optional
from urllib.parse import urlencode, urljoin

import opentracing
import opentracing.tags
from django.contrib.auth.hashers import make_password
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import reverse
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
from ..utils import get_supported_currencies, require_active_plugin
from .utils.apple_pay import initialize_apple_pay, make_request_to_initialize_apple_pay
from .utils.common import (
    AUTH_STATUS,
    FAILED_STATUSES,
    PENDING_STATUSES,
    api_call,
    call_capture,
    call_refund,
    get_payment_method_info,
    get_request_data_for_check_payment,
    initialize_adyen_client,
    request_data_for_gateway_config,
    request_data_for_payment,
    request_for_payment_cancel,
    update_payment_with_action_required_data,
)
from .webhooks import handle_additional_actions, handle_webhook

GATEWAY_NAME = "Adyen"
WEBHOOK_PATH = "/webhooks"
ADDITIONAL_ACTION_PATH = "/additional-actions"


class AdyenGatewayPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.payments.adyen"
    PLUGIN_NAME = GATEWAY_NAME
    CONFIGURATION_PER_CHANNEL = True
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
            "help_text": "Your merchant account name.",
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
                "ions-in-your-customer-area."
            ),
            "label": "HMAC secret key",
        },
        "notification-user": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Base User provided on the Adyen side to authenticate incoming "
                "notifications. https://docs.adyen.com/development-resources/webhooks#"
                "set-up-notifications-in-your-customer-area "
            ),
            "label": "Notification user",
        },
        "notification-password": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "User password provided on the Adyen side for authenticate incoming "
                "notifications. https://docs.adyen.com/development-resources/webhooks#"
                "set-up-notifications-in-your-customer-area "
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
        "webhook-endpoint": {
            "type": ConfigurationTypeField.OUTPUT,
            "help_text": (
                "Endpoint which should be used to activate Adyen's webhooks. "
                "More details can be find here: "
                "https://docs.adyen.com/development-resources/webhooks"
            ),
            "label": "Webhook endpoint",
        },
    }

    def __init__(self, *args, **kwargs):
        channel = kwargs["channel"]
        raw_configuration = kwargs["configuration"].copy()
        self._insert_webhook_endpoint_to_configuration(raw_configuration, channel)
        kwargs["configuration"] = raw_configuration

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
        self.adyen = initialize_adyen_client(self.config)

    def _insert_webhook_endpoint_to_configuration(self, raw_configuration, channel):
        updated = False
        for config in raw_configuration:
            if config["name"] == "webhook-endpoint":
                updated = True
                config["value"] = self._generate_webhook_url(channel)
        if not updated:
            raw_configuration.append(
                {
                    "name": "webhook-endpoint",
                    "value": self._generate_webhook_url(channel),
                }
            )

    def _generate_webhook_url(self, channel) -> str:
        api_path = reverse(
            "plugins-per-channel",
            kwargs={"plugin_id": self.PLUGIN_ID, "channel_slug": channel.slug},
        )
        base_url = build_absolute_uri(api_path)
        return urljoin(base_url, "webhooks")  # type: ignore

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        """Handle a request received from Adyen.

        The method handles two types of requests:
            - webhook notification received from Adyen. It is required to properly
            update the current status of payment and order based on the type of
            received notification.
            - additional actions, called when a user is redirected to an external page
            and after processing a payment is redirecting back to the storefront page.
            The redirect request comes through the Saleor which calls Adyen API to
            validate the current status of payment.
        """
        config = self._get_gateway_config()
        if path.startswith(WEBHOOK_PATH):
            return handle_webhook(request, config)
        elif path.startswith(ADDITIONAL_ACTION_PATH):
            with opentracing.global_tracer().start_active_span(
                "adyen.checkout.payment_details"
            ) as scope:
                span = scope.span
                span.set_tag(opentracing.tags.COMPONENT, "payment")
                span.set_tag("service.name", "adyen")
                return handle_additional_actions(
                    request,
                    self.adyen.checkout.payments_details,
                    self.channel.slug,  # type: ignore
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
        """Initialize a payment for ApplePay.

        ApplePay requires an additional action that initializes a payment action. It is
        done by a separate mutation which calls this method.
        """
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
    def get_payment_gateways(
        self, currency: Optional[str], checkout: Optional["Checkout"], previous_value
    ) -> List["PaymentGateway"]:
        """Fetch current configuration for given checkout.

        It calls an Adyen API to fetch all available payment methods for given checkout.
        Adyen defines available payment methods based on the data that we send like
        amount, currency, and country. Some payment methods are only available if the
        given data matches their conditions. Like to display payment method X, which is
        available in UK, we need to set GBP as currency, and country-code needs to
        point to UK. We don't fetch anything if checkout is none, as we don't have
        enough info to provide the required data in the request.
        """
        local_config = self._get_gateway_config()
        config = [
            {
                "field": "client_key",
                "value": local_config.connection_params["client_key"],
            }
        ]

        if checkout:
            # If checkout is available, fetch available payment methods from Adyen API
            # and append them to the config object returned for the gateway.
            request = request_data_for_gateway_config(
                checkout, local_config.connection_params["merchant_account"]
            )
            with opentracing.global_tracer().start_active_span(
                "adyen.checkout.payment_methods"
            ) as scope:
                span = scope.span
                span.set_tag(opentracing.tags.COMPONENT, "payment")
                span.set_tag("service.name", "adyen")
                response = api_call(request, self.adyen.checkout.payment_methods)
                adyen_payment_methods = json.dumps(response.message)
                config.append({"field": "config", "value": adyen_payment_methods})

        gateway = PaymentGateway(
            id=self.PLUGIN_ID,
            name=self.PLUGIN_NAME,
            config=config,
            currencies=self.get_supported_currencies([]),
        )
        return [gateway]

    @require_active_plugin
    def check_payment_balance(self, data: dict, previous_value=None) -> dict:
        """Check current payment balance.

        For Adyen, we use it only for checking the balance of the gift cards. It builds
        a request based on the input and send a request to Adyen's API.
        """
        request_data = get_request_data_for_check_payment(
            data, self.config.connection_params["merchant_account"]
        )

        with opentracing.global_tracer().start_active_span(
            "adyen.checkout.payment_methods_balance"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "payment")
            span.set_tag("service.name", "adyen")

            try:
                result = api_call(
                    request_data,
                    self.adyen.checkout.client.call_checkout_api,
                    action="paymentMethods/balance",
                )
                return result.message
            except PaymentError as e:
                return e.message

    @property
    def order_auto_confirmation(self):
        site_settings = Site.objects.get_current().settings
        return site_settings.automatically_confirm_all_new_orders

    @require_active_plugin
    def process_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        """Process a payment on Adyen's side.

        This method is called when payment.to_confirm is set to False.
        It builds a request data required for a given payment method and sends the data
        to Adyen's side.
        If Adyen doesn't return any additional action required and the result code is
        a success, the payment is finalized with success. If auto_capture is set to
        True, and the payment status is AUTH, it will immediately call capture.
        If Adyen returns an additional action to process by customer, the payment is
        not finished yet. In that case, in the response from the method, we set
        action_required and add to action_required_data all Adyen's data required to
        finalize payment by the customer.
        """
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
                f"/plugins/channel/{self.channel.slug}/"  # type: ignore
                f"{self.PLUGIN_ID}/additional-actions"
            ),
        )
        request_data = request_data_for_payment(
            payment_information,
            return_url=return_url,
            merchant_account=self.config.connection_params["merchant_account"],
            native_3d_secure=self.config.connection_params["enable_native_3d_secure"],
        )
        with opentracing.global_tracer().start_active_span(
            "adyen.checkout.payments"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "payment")
            span.set_tag("service.name", "adyen")
            result = api_call(request_data, self.adyen.checkout.payments)
        result_code = result.message["resultCode"].strip().lower()
        is_success = result_code not in FAILED_STATUSES
        adyen_auto_capture = self.config.connection_params["adyen_auto_capture"]
        kind = TransactionKind.AUTH
        if result_code in PENDING_STATUSES:
            kind = TransactionKind.PENDING
        elif adyen_auto_capture:
            kind = TransactionKind.CAPTURE
        psp_reference = result.message.get("pspReference", "")
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
            psp_reference=psp_reference,
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
            return GatewayResponse(
                is_success=False,
                action_required=False,
                kind=kind,
                amount=payment_information.amount,
                currency=payment_information.currency,
                transaction_id="",
                error=f"Unable to finish the payment. "
                f"Payment ({payment_information.graphql_payment_id}) "
                f"does not have the additional data.",
            )

        with opentracing.global_tracer().start_active_span(
            "adyen.checkout.payment_details"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "payment")
            span.set_tag("service.name", "adyen")
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
            psp_reference=result.message.get("pspReference", ""),
            payment_method_info=payment_method_info,
        )

    @require_active_plugin
    def confirm_payment(
        self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        """Confirm a payment on Adyen side.

        In case when we have a transaction with `ACTION_TO_CONFIRM`, we just need to
        finalize the payment process on our side. Transaction ACTION_TO_CONFIRM is
        created only when we receive a webhook with a notification that the payment
        process has been finished with success.
        In case when we can't find an ACTION_TO_CONFIRM transaction, we call logic
        responsible for confirming additional data received as an input. The data
        comes from the storefront when the customer finishes an additional action,
        which was requested in process_payment call. We still check the value of the
        action field in the Adyen's response, as there is a possibility that the given
        payment method will require more additional actions. In that case, we will
        return action_required set to True and action_required_data fulfilled with
        action data received from Adyen and required for the next additional action on
        the customer side.
        """
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
        payment_method = (
            transaction.gateway_response.get("paymentMethod", "").strip().lower()
        )
        if result_code and result_code in PENDING_STATUSES:
            kind = TransactionKind.PENDING
        elif result_code == AUTH_STATUS and payment_method == "ideal":
            kind = TransactionKind.CAPTURE

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

        amount = payment_information.amount
        currency = payment_information.currency

        result = call_refund(
            amount=amount,
            currency=currency,
            graphql_payment_id=payment_information.graphql_payment_id,
            merchant_account=self.config.connection_params["merchant_account"],
            token=transaction.token,
            adyen_client=self.adyen,
        )

        if transaction.payment.order:
            msg = f"Adyen: Refund for amount {amount}{currency} has been requested."
            external_notification_event(
                order=transaction.payment.order,  # type: ignore
                user=None,
                app=None,
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
            psp_reference=result.message.get("pspReference", ""),
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
            psp_reference=result.message.get("pspReference", ""),
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
        with opentracing.global_tracer().start_active_span(
            "adyen.payment.cancel"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "payment")
            span.set_tag("service.name", "adyen")
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
            psp_reference=result.message.get("pspReference", ""),
        )

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
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
