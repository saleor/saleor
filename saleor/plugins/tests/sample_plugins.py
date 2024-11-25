from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from graphene import Mutation
from graphql import GraphQLError, ResolveInfo
from graphql.execution import ExecutionResult
from prices import Money, TaxedMoney

from ...account.models import User
from ...core.taxes import TaxData, TaxLineData, TaxType
from ...order.interface import OrderTaxedPricesData
from ...payment.interface import (
    PaymentGatewayData,
    TransactionSessionData,
    TransactionSessionResult,
)
from ..base_plugin import BasePlugin, ConfigurationTypeField, ExternalAccessTokens

if TYPE_CHECKING:
    from ...account.models import Address
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...checkout.models import Checkout
    from ...core.models import EventDelivery
    from ...discount.models import Promotion
    from ...order.models import Order, OrderLine
    from ...product.models import Product, ProductVariant


def sample_tax_data(obj_with_lines: Union["Order", "Checkout"]) -> TaxData:
    unit = Decimal("10.00")
    unit_gross = Decimal("12.30")
    lines = [
        TaxLineData(
            total_net_amount=unit * 3,
            total_gross_amount=unit_gross * 3,
            tax_rate=Decimal("23"),
        )
        for _ in obj_with_lines.lines.all()
    ]

    shipping = Decimal("50.00")
    shipping_gross = Decimal("63.20")

    return TaxData(
        shipping_price_net_amount=shipping,
        shipping_price_gross_amount=shipping_gross,
        shipping_tax_rate=Decimal("23"),
        lines=lines,
    )


class PluginSample(BasePlugin):
    PLUGIN_ID = "plugin.sample"
    PLUGIN_NAME = "PluginSample"
    PLUGIN_DESCRIPTION = "Test plugin description"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False
    DEFAULT_CONFIGURATION = [
        {"name": "Username", "value": "admin"},
        {"name": "Password", "value": None},
        {"name": "Use sandbox", "value": False},
        {"name": "API private key", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "Username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Username input field",
            "label": "Username",
        },
        "Password": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": "Password input field",
            "label": "Password",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Use sandbox",
            "label": "Use sandbox",
        },
        "API private key": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "API key",
            "label": "Private key",
        },
        "certificate": {
            "type": ConfigurationTypeField.SECRET_MULTILINE,
            "help_text": "",
            "label": "Multiline certificate",
        },
    }

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path == "/webhook/paid":
            return JsonResponse(data={"received": True, "paid": True})
        if path == "/webhook/failed":
            return JsonResponse(data={"received": True, "paid": False})
        return HttpResponseNotFound()

    def calculate_checkout_total(self, checkout_info, lines, address, previous_value):
        total = Money("1.0", currency=checkout_info.checkout.currency)
        return TaxedMoney(total, total)

    def calculate_checkout_shipping(
        self, checkout_info, lines, address, previous_value
    ):
        price = Money("1.0", currency=checkout_info.checkout.currency)
        return TaxedMoney(price, price)

    def calculate_order_shipping(self, order, previous_value):
        price = Money("1.0", currency=order.currency)
        return TaxedMoney(price, price)

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: TaxedMoney,
    ):
        # See if delivery method doesn't trigger infinite recursion
        bool(checkout_info.delivery_method_info.delivery_method)

        price = Money("1.0", currency=checkout_info.checkout.currency)
        return TaxedMoney(price, price)

    def calculate_order_line_total(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        price = Money("1.0", currency=order.currency)
        return OrderTaxedPricesData(
            price_with_discounts=TaxedMoney(price, price),
            undiscounted_price=TaxedMoney(price, price),
        )

    def calculate_checkout_line_unit_price(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: TaxedMoney,
    ):
        currency = checkout_info.checkout.currency
        price = Money("10.0", currency)
        return TaxedMoney(price, price)

    def calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ):
        currency = order_line.unit_price.currency
        price = Money("1.0", currency)
        return OrderTaxedPricesData(
            price_with_discounts=TaxedMoney(price, price),
            undiscounted_price=TaxedMoney(price, price),
        )

    def get_tax_rate_type_choices(self, previous_value):
        return [TaxType(code="123", description="abc")]

    def external_authentication_url(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        return {"authorizeUrl": "http://www.auth.provider.com/authorize/"}

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        return ExternalAccessTokens(
            token="token1", refresh_token="refresh2", csrf_token="csrf3"
        )

    def external_refresh(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        return ExternalAccessTokens(
            token="token4", refresh_token="refresh5", csrf_token="csrf6"
        )

    def external_verify(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> tuple[Optional[User], dict]:
        user = User.objects.get()
        return user, {"some_data": "data"}

    def authenticate_user(
        self, request: WSGIRequest, previous_value
    ) -> Optional["User"]:
        return User.objects.filter().first()

    def external_logout(self, data: dict, request: WSGIRequest, previous_value) -> dict:
        return {"logoutUrl": "http://www.auth.provider.com/logout/"}

    def sale_created(
        self,
        sale: "Promotion",
        current_catalogue: defaultdict[str, set[str]],
        previous_value: Any,
    ):
        return sale, current_catalogue

    def sale_updated(
        self,
        sale: "Promotion",
        previous_catalogue: defaultdict[str, set[str]],
        current_catalogue: defaultdict[str, set[str]],
        previous_value: Any,
    ):
        return sale, previous_catalogue, current_catalogue

    def sale_deleted(
        self,
        sale: "Promotion",
        previous_catalogue: defaultdict[str, set[str]],
        previous_value: Any,
    ):
        return sale, previous_catalogue

    def sale_toggle(
        self,
        sale: "Promotion",
        catalogue: defaultdict[str, set[str]],
        previous_value: Any,
        webhooks,
    ):
        return sale, catalogue

    def promotion_created(self, promotion: "Promotion", previous_value: Any):
        return None

    def promotion_updated(self, promotion: "Promotion", previous_value: Any):
        return None

    def promotion_deleted(self, promotion: "Promotion", previous_value: Any):
        return None

    def promotion_started(self, promotion: "Promotion", previous_value: Any):
        return None

    def promotion_ended(self, promotion: "Promotion", previous_value: Any):
        return None

    def product_variant_stock_updated(self, stock, previous_value: Any):
        return None

    def translation_created(self, translation, previous_value: Any):
        return None

    def translation_updated(self, translation, previous_value: Any):
        return None

    def get_checkout_line_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: Decimal,
    ) -> Decimal:
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_order_line_tax_rate(
        self,
        order: "Order",
        product: "Product",
        variant: "ProductVariant",
        address: Optional["Address"],
        previous_value: Decimal,
    ) -> Decimal:
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_checkout_shipping_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        previous_value: Decimal,
    ):
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_order_shipping_tax_rate(self, order: "Order", previous_value: Decimal):
        return Decimal("0.080").quantize(Decimal(".01"))

    def get_taxes_for_checkout(
        self,
        checkout_info: "CheckoutInfo",
        lines,
        app_identifier,
        previous_value,
        pregenerated_subscription_payloads=None,
    ) -> Optional["TaxData"]:
        return sample_tax_data(checkout_info.checkout)

    def get_taxes_for_order(
        self, order: "Order", app_identifier, previous_value
    ) -> Optional["TaxData"]:
        return sample_tax_data(order)

    def sample_not_implemented(self, previous_value):
        return NotImplemented

    def event_delivery_retry(self, delivery: "EventDelivery", previous_value: Any):
        return True

    def perform_mutation(
        self,
        mutation_cls: Mutation,
        root,
        info: ResolveInfo,
        data: dict,
        previous_value: Optional[Union[ExecutionResult, GraphQLError]],
    ) -> Optional[Union[ExecutionResult, GraphQLError]]:
        return None

    def payment_gateway_initialize_session(
        self,
        amount: Decimal,
        payment_gateways: Optional[list["PaymentGatewayData"]],
        source_object: Union["Order", "Checkout"],
        previous_value: Any,
    ):
        return [PaymentGatewayData(app_identifier="123", data={"some": "json-data"})]

    def transaction_initialize_session(
        self,
        transaction_session_data: "TransactionSessionData",
        previous_value: Any,
    ):
        return TransactionSessionResult(
            app_identifier="123", response=None, error="Some error"
        )

    def transaction_process_session(
        self,
        transaction_session_data: "TransactionSessionData",
        previous_value: Any,
    ):
        return TransactionSessionResult(
            app_identifier="321", response=None, error="Some error"
        )

    def checkout_fully_paid(self, checkout, previous_value, webhooks):
        return None

    def order_fully_refunded(self, order, previous_value, webhooks):
        return None

    def order_paid(self, order, previous_value):
        return None

    def order_refunded(self, order, previous_value, webhooks):
        return None

    def list_stored_payment_methods(
        self,
        list_payment_method_data,
        previous_value,
    ):
        return []

    def stored_payment_method_request_delete(self, request_delete_data, previous_value):
        return previous_value

    def payment_gateway_initialize_tokenization(self, request_data, previous_value):
        return previous_value

    def payment_method_initialize_tokenization(self, request_data, previous_value):
        return previous_value

    def payment_method_process_tokenization(self, request_data, previous_value):
        return previous_value


class ChannelPluginSample(PluginSample):
    PLUGIN_ID = "channel.plugin.sample"
    PLUGIN_NAME = "Channel Plugin"
    PLUGIN_DESCRIPTION = "Test channel plugin"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = True
    DEFAULT_CONFIGURATION = [{"name": "input-per-channel", "value": None}]
    CONFIG_STRUCTURE = {
        "input-per-channel": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Test input",
            "label": "Input per channel",
        }
    }


class InactiveChannelPluginSample(PluginSample):
    PLUGIN_ID = "channel.plugin.inactive.sample"
    PLUGIN_NAME = "Inactive Channel Plugin"
    PLUGIN_DESCRIPTION = "Test channel plugin"
    DEFAULT_ACTIVE = False
    CONFIGURATION_PER_CHANNEL = True
    DEFAULT_CONFIGURATION = [{"name": "input-per-channel", "value": None}]
    CONFIG_STRUCTURE = {
        "input-per-channel": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Test input",
            "label": "Input per channel",
        }
    }


class PluginInactive(BasePlugin):
    PLUGIN_ID = "mirumee.taxes.plugin.inactive"
    PLUGIN_NAME = "PluginInactive"
    PLUGIN_DESCRIPTION = "Test plugin description_2"
    CONFIGURATION_PER_CHANNEL = False
    DEFAULT_ACTIVE = False

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        return ExternalAccessTokens(
            token="token1", refresh_token="refresh2", csrf_token="csrf3"
        )


class ActivePlugin(BasePlugin):
    PLUGIN_ID = "mirumee.x.plugin.active"
    PLUGIN_NAME = "Active"
    PLUGIN_DESCRIPTION = "Not working"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False


class ActivePaymentGateway(BasePlugin):
    PLUGIN_ID = "mirumee.gateway.active"
    CLIENT_CONFIG = [
        {"field": "foo", "value": "bar"},
    ]
    PLUGIN_NAME = "braintree"
    DEFAULT_ACTIVE = True
    SUPPORTED_CURRENCIES = ["USD"]

    def process_payment(self, payment_information, previous_value):
        pass

    def get_supported_currencies(self, previous_value):
        return self.SUPPORTED_CURRENCIES

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG


class ActiveDummyPaymentGateway(BasePlugin):
    PLUGIN_ID = "sampleDummy.active"
    CLIENT_CONFIG = [
        {"field": "foo", "value": "bar"},
    ]
    PLUGIN_NAME = "SampleDummy"
    DEFAULT_ACTIVE = True
    SUPPORTED_CURRENCIES = ["EUR", "USD"]

    def process_payment(self, payment_information, previous_value):
        pass

    def get_supported_currencies(self, previous_value):
        return self.SUPPORTED_CURRENCIES

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG

    def check_payment_balance(self, request_data: dict, previous_value):
        return {"test_response": "success"}


class SampleAuthorizationPlugin(BasePlugin):
    PLUGIN_ID = "saleor.sample.authorization"
    PLUGIN_NAME = "SampleAuthorization"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    def authenticate_user(self, request, previous_value) -> Optional[User]:
        # This function will be mocked in test
        raise NotImplementedError()


class InactivePaymentGateway(BasePlugin):
    PLUGIN_ID = "gateway.inactive"
    PLUGIN_NAME = "stripe"
    DEFAULT_ACTIVE = False
    SUPPORTED_CURRENCIES = []
    CLIENT_CONFIG = []

    def process_payment(self, payment_information, previous_value):
        pass

    def get_supported_currencies(self, previous_value):
        return self.SUPPORTED_CURRENCIES

    def get_payment_config(self, previous_value):
        return self.CLIENT_CONFIG


ACTIVE_PLUGINS = (
    ChannelPluginSample,
    ActivePaymentGateway,
    ActivePlugin,
    ActiveDummyPaymentGateway,
)

INACTIVE_PLUGINS = (
    InactivePaymentGateway,
    PluginInactive,
    InactiveChannelPluginSample,
)

ALL_PLUGINS = ACTIVE_PLUGINS + INACTIVE_PLUGINS
