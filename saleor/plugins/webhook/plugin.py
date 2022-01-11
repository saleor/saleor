import json
import logging
from typing import TYPE_CHECKING, Any, List, Optional

from ...app.models import App
from ...core.utils.json_serializer import CustomJsonEncoder
from ...payment import PaymentError, TransactionKind
from ...shipping.interface import ShippingMethodData
from ...webhook.event_types import WebhookEventType
from ...webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_excluded_shipping_methods_for_checkout_payload,
    generate_excluded_shipping_methods_for_order_payload,
    generate_fulfillment_payload,
    generate_invoice_payload,
    generate_list_gateways_payload,
    generate_order_payload,
    generate_page_payload,
    generate_payment_payload,
    generate_product_deleted_payload,
    generate_product_payload,
    generate_product_variant_payload,
    generate_translation_payload,
)
from ..base_plugin import BasePlugin, ExcludedShippingMethod
from .const import CACHE_EXCLUDED_SHIPPING_KEY
from .tasks import (
    _get_webhooks_for_event,
    trigger_webhook_sync,
    trigger_webhooks_for_event,
)
from .utils import (
    from_payment_app_id,
    get_excluded_shipping_data,
    parse_list_payment_gateways_response,
    parse_payment_action_response,
)

if TYPE_CHECKING:
    from ...account.models import User
    from ...checkout.models import Checkout
    from ...core.notify_events import NotifyEventType
    from ...invoice.models import Invoice
    from ...order.models import Fulfillment, Order
    from ...page.models import Page
    from ...payment.interface import GatewayResponse, PaymentData, PaymentGateway
    from ...product.models import Product, ProductVariant
    from ...translation.models import Translation


logger = logging.getLogger(__name__)


class WebhookPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.webhooks"
    PLUGIN_NAME = "Webhooks"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    @classmethod
    def check_plugin_id(cls, plugin_id: str) -> bool:
        is_webhook_plugin = super().check_plugin_id(plugin_id)
        if not is_webhook_plugin:
            payment_app_data = from_payment_app_id(plugin_id)
            return payment_app_data is not None
        return is_webhook_plugin

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.ORDER_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.ORDER_CONFIRMED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.ORDER_FULLY_PAID
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.ORDER_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.INVOICE_REQUESTED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_invoice_payload(invoice), list(webhooks)
            )

    def invoice_delete(self, invoice: "Invoice", previous_value: Any):
        if not self.active:
            return previous_value
        event_type = WebhookEventType.INVOICE_DELETED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_invoice_payload(invoice), list(webhooks)
            )

    def invoice_sent(self, invoice: "Invoice", email: str, previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.INVOICE_SENT
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_invoice_payload(invoice), list(webhooks)
            )

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.ORDER_CANCELLED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.ORDER_FULFILLED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def draft_order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.DRAFT_ORDER_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def draft_order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.DRAFT_ORDER_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def draft_order_deleted(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.DRAFT_ORDER_DELETED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_order_payload(order), list(webhooks)
            )

    def fulfillment_created(self, fulfillment: "Fulfillment", previous_value):
        if not self.active:
            return previous_value
        event_type = WebhookEventType.FULFILLMENT_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_fulfillment_payload(fulfillment), list(webhooks)
            )

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.CUSTOMER_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_customer_payload(customer), list(webhooks)
            )

    def customer_updated(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.CUSTOMER_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_customer_payload(customer), list(webhooks)
            )

    def product_created(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PRODUCT_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_product_payload(product), list(webhooks)
            )

    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PRODUCT_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_product_payload(product), list(webhooks)
            )

    def product_deleted(
        self, product: "Product", variants: List[int], previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PRODUCT_DELETED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type,
                generate_product_deleted_payload(product, variants),
                list(webhooks),
            )

    def product_variant_created(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PRODUCT_VARIANT_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type,
                generate_product_variant_payload([product_variant]),
                list(webhooks),
            )

    def product_variant_updated(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PRODUCT_VARIANT_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type,
                generate_product_variant_payload([product_variant]),
                list(webhooks),
            )

    def product_variant_deleted(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PRODUCT_VARIANT_DELETED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type,
                generate_product_variant_payload([product_variant]),
                list(webhooks),
            )

    def checkout_created(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.CHECKOUT_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_checkout_payload(checkout), list(webhooks)
            )

    def checkout_updated(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.CHECKOUT_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_checkout_payload(checkout), list(webhooks)
            )

    def notify(self, event: "NotifyEventType", payload: dict, previous_value) -> Any:
        if not self.active:
            return previous_value
        data = {"notify_event": event, "payload": payload}
        trigger_webhooks_for_event.delay(
            WebhookEventType.NOTIFY_USER, json.dumps(data, cls=CustomJsonEncoder)
        )

    def page_created(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PAGE_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_page_payload(page), list(webhooks)
            )

    def page_updated(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PAGE_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_page_payload(page), list(webhooks)
            )

    def page_deleted(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        event_type = WebhookEventType.PAGE_DELETED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_page_payload(page), list(webhooks)
            )

    def translation_created(self, translation: "Translation", previous_value: Any):
        if not self.active:
            return previous_value
        event_type = WebhookEventType.TRANSLATION_CREATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_translation_payload(translation), list(webhooks)
            )

    def translation_updated(self, translation: "Translation", previous_value: Any):
        if not self.active:
            return previous_value
        event_type = WebhookEventType.TRANSLATION_UPDATED
        if webhooks := _get_webhooks_for_event(event_type):
            trigger_webhooks_for_event.delay(
                event_type, generate_translation_payload(translation), list(webhooks)
            )

    def __run_payment_webhook(
        self,
        event_type: str,
        transaction_kind: str,
        payment_information: "PaymentData",
        previous_value,
        **kwargs
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value

        app = None
        payment_app_data = from_payment_app_id(payment_information.gateway)

        if payment_app_data is not None:
            app = (
                App.objects.for_event_type(event_type)
                .filter(pk=payment_app_data.app_pk)
                .first()
            )

        if not app:
            logger.warning(
                "Payment webhook for event %r failed - no active app found: %r",
                event_type,
                payment_information.gateway,
            )
            raise PaymentError(
                f"Payment method {payment_information.gateway} is not available: "
                "app not found."
            )

        webhook_payload = generate_payment_payload(payment_information)
        response_data = trigger_webhook_sync(event_type, webhook_payload, app)
        if response_data is None:
            raise PaymentError(
                f"Payment method {payment_information.gateway} is not available: "
                "no response from the app."
            )

        return parse_payment_action_response(
            payment_information, response_data, transaction_kind
        )

    def token_is_required_as_payment_input(self, previous_value):
        return False

    def get_payment_gateways(
        self,
        currency: Optional[str],
        checkout: Optional["Checkout"],
        previous_value,
        **kwargs
    ) -> List["PaymentGateway"]:
        gateways = []
        apps = App.objects.for_event_type(
            WebhookEventType.PAYMENT_LIST_GATEWAYS
        ).prefetch_related("webhooks")
        for app in apps:
            response_data = trigger_webhook_sync(
                event_type=WebhookEventType.PAYMENT_LIST_GATEWAYS,
                data=generate_list_gateways_payload(currency, checkout),
                app=app,
            )
            if response_data:
                app_gateways = parse_list_payment_gateways_response(response_data, app)
                if currency:
                    app_gateways = [
                        gtw for gtw in app_gateways if currency in gtw.currencies
                    ]
                gateways.extend(app_gateways)
        return gateways

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            previous_value,
            **kwargs,
        )

    def capture_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_CAPTURE,
            TransactionKind.CAPTURE,
            payment_information,
            previous_value,
            **kwargs,
        )

    def refund_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_REFUND,
            TransactionKind.REFUND,
            payment_information,
            previous_value,
            **kwargs,
        )

    def void_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_VOID,
            TransactionKind.VOID,
            payment_information,
            previous_value,
            **kwargs,
        )

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_CONFIRM,
            TransactionKind.CONFIRM,
            payment_information,
            previous_value,
            **kwargs,
        )

    def process_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_PROCESS,
            TransactionKind.CAPTURE,
            payment_information,
            previous_value,
            **kwargs,
        )

    def excluded_shipping_methods_for_order(
        self,
        order: "Order",
        available_shipping_methods: List[ShippingMethodData],
        previous_value: List[ExcludedShippingMethod],
    ) -> List[ExcludedShippingMethod]:
        generate_function = generate_excluded_shipping_methods_for_order_payload
        payload_fun = lambda: generate_function(  # noqa: E731
            order,
            available_shipping_methods,
        )
        cache_key = CACHE_EXCLUDED_SHIPPING_KEY + order.token
        return get_excluded_shipping_data(
            event_type=WebhookEventType.ORDER_FILTER_SHIPPING_METHODS,
            previous_value=previous_value,
            payload_fun=payload_fun,
            cache_key=cache_key,
        )

    def excluded_shipping_methods_for_checkout(
        self,
        checkout: "Checkout",
        available_shipping_methods: List[ShippingMethodData],
        previous_value: List[ExcludedShippingMethod],
    ) -> List[ExcludedShippingMethod]:
        generate_function = generate_excluded_shipping_methods_for_checkout_payload
        payload_function = lambda: generate_function(  # noqa: E731
            checkout,
            available_shipping_methods,
        )
        cache_key = CACHE_EXCLUDED_SHIPPING_KEY + str(checkout.token)
        return get_excluded_shipping_data(
            event_type=WebhookEventType.CHECKOUT_FILTER_SHIPPING_METHODS,
            previous_value=previous_value,
            payload_fun=payload_function,
            cache_key=cache_key,
        )

    def is_event_active(self, event: str, channel=Optional[str]):
        map_event = {"invoice_request": WebhookEventType.INVOICE_REQUESTED}
        webhooks = _get_webhooks_for_event(event_type=map_event[event])
        return any(webhooks)
