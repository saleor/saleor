import logging
from dataclasses import asdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union
from urllib.parse import urljoin

import opentracing
import opentracing.tags
from django.core.exceptions import ValidationError
from prices import Money, TaxedMoney

from ...checkout import base_calculations
from ...checkout.fetch import fetch_checkout_lines
from ...core.prices import quantize_price
from ...core.taxes import TaxError, zero_money, zero_taxed_money
from ...discount import DiscountInfo, OrderDiscountType
from ...order.interface import OrderTaxedPricesData
from ..avatax import _validate_checkout, _validate_order, api_get_request
from ..avatax.plugin import AvataxPlugin
from ..base_plugin import ConfigurationTypeField
from ..error_codes import PluginErrorCode
from .tasks import api_post_request_task
from .utils import (
    TRANSACTION_TYPE,
    AvataxConfiguration,
    api_post_request,
    generate_request_data_from_checkout,
    get_api_url,
    get_checkout_tax_data,
    get_order_request_data,
    get_order_tax_data,
    process_checkout_metadata,
)

if TYPE_CHECKING:
    from uuid import UUID

    from ...account.models import Address
    from ...channel.models import Channel
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...order.models import Order, OrderLine
    from ...plugins.models import PluginConfiguration
    from ...product.models import Product, ProductVariant

logger = logging.getLogger(__name__)


class AvataxExcisePlugin(AvataxPlugin):
    PLUGIN_NAME = "Avalara Excise"
    PLUGIN_ID = "mirumee.taxes.avalara_excise"

    DEFAULT_CONFIGURATION = [
        {"name": "Username or account", "value": None},
        {"name": "Password or license", "value": None},
        {"name": "Use sandbox", "value": True},
        {"name": "Company name", "value": ""},
        {"name": "Autocommit", "value": False},
        {"name": "Shipping Product Code", "value": "TAXFREIGHT"},
    ]
    CONFIG_STRUCTURE = {
        "Username or account": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide user details",
            "label": "Username",
        },
        "Password or license": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": "Provide password details",
            "label": "Password",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if .. should use Avatax " "Excise sandbox API.",
            "label": "Use sandbox",
        },
        "Company name": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Avalara company ID.",
            "label": "Company ID",
        },
        "Autocommit": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines, if order transactions sent to Avalara "
            "Excise should be committed by default.",
            "label": "Autocommit",
        },
        "Shipping Product Code": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Avalara Excise Product Code used to represent "
            "shipping. This Product should set the Avatax Tax Code to "
            "FR020000 or other freight tax code. See "
            "https://taxcode.avatax.avalara.com/tree"
            "?tree=freight-and-freight-related-charges&tab=interactive",
            "label": "Shipping Product Code",
        },
    }

    def __init__(self, *args, **kwargs):
        super(AvataxPlugin, self).__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = AvataxConfiguration(
            username_or_account=configuration["Username or account"],
            password_or_license=configuration["Password or license"],
            use_sandbox=configuration["Use sandbox"],
            company_name=configuration["Company name"],
            autocommit=configuration["Autocommit"],
            shipping_product_code=configuration["Shipping Product Code"],
        )

    @classmethod
    def validate_authentication(cls, plugin_configuration: "PluginConfiguration"):
        conf = {
            data["name"]: data["value"] for data in plugin_configuration.configuration
        }
        url = urljoin(get_api_url(conf["Use sandbox"]), "utilities/ping")
        response = api_get_request(
            url,
            username_or_account=conf["Username or account"],
            password_or_license=conf["Password or license"],
        )

        if not response.get("authenticated"):
            raise ValidationError(
                "Authentication failed. Please check provided data.",
                code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
            )

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
        """Validate if provided configuration is correct."""
        missing_fields = []
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if not configuration["Username or account"]:
            missing_fields.append("Username or account")
        if not configuration["Password or license"]:
            missing_fields.append("Password or license")

        if plugin_configuration.active:
            if missing_fields:
                error_msg = (
                    "To enable a plugin, you need to provide values for the "
                    "following fields: "
                )
                raise ValidationError(
                    error_msg + ", ".join(missing_fields),
                    code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                )

            cls.validate_authentication(plugin_configuration)

    def calculate_checkout_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        checkout_total = previous_value

        taxes_data = self._get_checkout_tax_data(
            checkout_info, lines, discounts, checkout_total
        )
        if not taxes_data:
            return checkout_total

        process_checkout_metadata(taxes_data, checkout_info.checkout)

        checkout = checkout_info.checkout
        currency = checkout.currency
        tax = Money(Decimal(taxes_data.get("TotalTaxAmount", 0.0)), currency)
        net = checkout_total.net
        gross = net + tax
        taxed_total = quantize_price(TaxedMoney(net=net, gross=gross), currency)
        total = self._append_prices_of_not_taxed_lines(
            taxed_total,
            lines,
            checkout_info.channel,
            discounts,
        )

        return max(total, zero_taxed_money(total.currency))

    def _append_prices_of_not_taxed_lines(
        self,
        price: TaxedMoney,
        lines: Iterable["CheckoutLineInfo"],
        channel: "Channel",
        discounts: Iterable[DiscountInfo],
    ):
        for line_info in lines:
            if line_info.product.charge_taxes:
                continue
            prices_data = base_calculations.calculate_base_line_total_price(
                line_info,
                channel,
                discounts,
            )
            price.gross.amount += prices_data.amount
            price.net.amount += prices_data.amount
        return price

    def _calculate_checkout_shipping(
        self, currency: str, lines: List[Dict], shipping_price: TaxedMoney
    ) -> TaxedMoney:
        shipping_tax = Decimal(0.0)
        shipping_net = shipping_price.net.amount
        for line in lines:
            if line["InvoiceLine"] == 0:
                shipping_net += Decimal(line["TaxAmount"])
                shipping_tax += Decimal(line["TaxAmount"])

        shipping_gross = Money(amount=shipping_net + shipping_tax, currency=currency)
        shipping_net = Money(amount=shipping_net, currency=currency)
        return TaxedMoney(net=shipping_net, gross=shipping_gross)

    def calculate_checkout_shipping(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        taxes_data = self._get_checkout_tax_data(
            checkout_info, lines, discounts, previous_value
        )
        if not taxes_data:
            return previous_value
        process_checkout_metadata(taxes_data, checkout_info.checkout)

        tax_lines = taxes_data.get("TransactionTaxes", [])
        if not tax_lines:
            return previous_value

        currency = checkout_info.checkout.currency
        return self._calculate_checkout_shipping(currency, tax_lines, previous_value)

    def preprocess_order_creation(
        self,
        checkout_info: "CheckoutInfo",
        discounts: Iterable["DiscountInfo"],
        lines: Optional[Iterable["CheckoutLineInfo"]],
        previous_value: Any,
    ):
        """Ensure all the data is correct and the order creation can be proceed.

        Raise an error when can't receive taxes.
        """
        if lines is None:
            lines, unavailable_variant_pks = fetch_checkout_lines(
                checkout_info.checkout
            )
            if unavailable_variant_pks:
                raise ValidationError(
                    "Some of the checkout lines variants are unavailable."
                )

        if self._skip_plugin(previous_value):
            return previous_value

        data = generate_request_data_from_checkout(
            checkout_info,
            lines_info=lines,
            config=self.config,
            transaction_type=TRANSACTION_TYPE,
            discounts=discounts,
        )
        if not data or not data.TransactionLines:
            return previous_value

        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox),
            "AvaTaxExcise/transactions/create",
        )
        with opentracing.global_tracer().start_active_span(
            "avatax_excise.transactions.create"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "tax")
            span.set_tag("service.name", "avatax_excise")
            taxes_data = api_post_request(transaction_url, data, self.config)
        if not taxes_data or taxes_data.get("Status") != "Success":
            transaction_errors = taxes_data.get("TransactionErrors")
            customer_msg = ""
            if isinstance(transaction_errors, list):
                for error in transaction_errors:
                    error_message = error.get("ErrorMessage")
                    if error_message:
                        customer_msg += error_message
                    error_code = taxes_data.get("ErrorCode", "")
                    logger.warning(
                        "Unable to calculate taxes for checkout %s"
                        "error_code: %s error_msg: %s",
                        checkout_info.checkout.token,
                        error_code,
                        error_message,
                    )
                    if error_code == "-1003":
                        raise ValidationError(error_message)
            raise TaxError(customer_msg)
        return previous_value

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value

        request_data = get_order_request_data(order, self.config)
        if not request_data:
            return previous_value
        base_url = get_api_url(self.config.use_sandbox)
        transaction_url = urljoin(
            base_url,
            "AvaTaxExcise/transactions/create",
        )
        commit_url = urljoin(
            base_url,
            "AvaTaxExcise/transactions/{}/commit",
        )

        api_post_request_task.delay(
            transaction_url,
            asdict(request_data),
            asdict(self.config),
            order.id,
            commit_url,
        )

        return previous_value

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        return previous_value

    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        return previous_value

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if not checkout_line_info.product.charge_taxes:
            return previous_value

        taxes_data = self._get_checkout_tax_data(
            checkout_info, lines, discounts, previous_value
        )
        if not taxes_data:
            return previous_value
        process_checkout_metadata(taxes_data, checkout_info.checkout)
        return self._calculate_checkout_line_total(
            taxes_data, lines, checkout_line_info.line.id, previous_value
        )

    @staticmethod
    def _calculate_checkout_line_total(
        taxes_data: Dict[str, Any],
        lines: Iterable["CheckoutLineInfo"],
        line_id: "UUID",
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if not taxes_data or "error" in taxes_data:
            return previous_value

        line_id_to_seq_number = {
            line_info.line.id: n + 1 for n, line_info in enumerate(lines)
        }
        sequence_id = line_id_to_seq_number.get(line_id)
        if sequence_id is None:
            return previous_value

        tax = Decimal("0.00")
        currency = ""
        for line in taxes_data.get("TransactionTaxes", []):
            if line.get("InvoiceLine") == sequence_id:
                tax += Decimal(line.get("TaxAmount", "0.00"))
                if not currency:
                    currency = line.get("Currency")

        if tax > 0 and currency:
            net = Decimal(previous_value.net.amount)

            line_net = Money(amount=net, currency=currency)
            line_gross = Money(amount=net + tax, currency=currency)
            return TaxedMoney(net=line_net, gross=line_gross)

        return previous_value

    def calculate_order_line_total(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        if self._skip_plugin(previous_value):
            return previous_value

        if not product.charge_taxes:
            return previous_value

        if not _validate_order(order):
            zero_money = zero_taxed_money(order.currency)
            return OrderTaxedPricesData(
                price_with_discounts=zero_money, undiscounted_price=zero_money
            )

        taxes_data = self._get_order_tax_data(order, previous_value)
        if not taxes_data:
            return previous_value
        return self._calculate_order_line_total(
            taxes_data, order, order_line.id, previous_value
        )

    @staticmethod
    def _calculate_order_line_total(
        taxes_data: Dict[str, Any],
        order: "Order",
        line_id: "UUID",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        if not taxes_data or "error" in taxes_data:
            return previous_value

        # lines order must be the same as used in request order data
        line_ids_sequence = list(
            order.lines.order_by("created_at").values_list("id", flat=True)
        )
        if line_id not in line_ids_sequence:
            return previous_value

        sequence_id = line_ids_sequence.index(line_id)

        tax = Decimal("0.00")
        currency = ""
        for line in taxes_data.get("TransactionTaxes", []):
            if line.get("InvoiceLine") == sequence_id:
                tax += Decimal(line.get("TaxAmount", "0.00"))
                if not currency:
                    currency = line.get("Currency")

        if tax > 0 and currency:
            net = Decimal(previous_value.price_with_discounts.net.amount)

            line_net = Money(amount=net, currency=currency)
            line_gross = Money(amount=net + tax, currency=currency)
            price_with_discounts = TaxedMoney(net=line_net, gross=line_gross)
            return OrderTaxedPricesData(
                price_with_discounts=price_with_discounts,
                undiscounted_price=previous_value.undiscounted_price,
            )

        return previous_value

    def calculate_checkout_line_unit_price(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        return previous_value

    def calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        if not variant or (variant and not product.charge_taxes):
            return previous_value

        quantity = order_line.quantity
        taxes_data = self._get_order_tax_data(order, previous_value)
        if not taxes_data:
            return previous_value
        default_total = OrderTaxedPricesData(
            price_with_discounts=previous_value.price_with_discounts * quantity,
            undiscounted_price=previous_value.undiscounted_price * quantity,
        )
        taxed_total_prices_data = self._calculate_order_line_total(
            taxes_data, order, order_line.id, default_total
        )
        return OrderTaxedPricesData(
            undiscounted_price=taxed_total_prices_data.undiscounted_price / quantity,
            price_with_discounts=taxed_total_prices_data.price_with_discounts
            / quantity,
        )

    def calculate_order_shipping(
        self, order: "Order", previous_value: TaxedMoney
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        if not _validate_order(order):
            return zero_taxed_money(order.total.currency)

        taxes_data = self._get_order_tax_data(order, previous_value)
        if not taxes_data:
            return previous_value
        tax_lines = taxes_data.get("TransactionTaxes", [])
        if not tax_lines:
            return previous_value

        currency = order.currency
        return self._calculate_checkout_shipping(currency, tax_lines, previous_value)

    def calculate_order_total(
        self,
        order: "Order",
        lines: Iterable["OrderLine"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        taxes_data = self._get_order_tax_data(order, previous_value)
        if not taxes_data:
            return previous_value

        currency = order.currency
        taxed_subtotal = zero_taxed_money(currency)

        for line in lines:
            base_line_price = OrderTaxedPricesData(
                undiscounted_price=line.undiscounted_total_price,
                price_with_discounts=TaxedMoney(
                    line.base_unit_price, line.base_unit_price
                )
                * line.quantity,
            )
            taxed_line_total_data = self._calculate_order_line_total(
                taxes_data,
                order,
                line.id,
                base_line_price,
            ).price_with_discounts
            taxed_subtotal += taxed_line_total_data

        shipping_price = self._calculate_order_shipping(
            order, taxes_data, order.base_shipping_price
        )

        discount_amount = zero_money(currency)
        order_discount = order.discounts.filter(type=OrderDiscountType.MANUAL).first()
        if order_discount:
            discount_amount = order_discount.amount

        taxed_total = taxed_subtotal + shipping_price - discount_amount

        return max(
            taxed_total,
            zero_taxed_money(currency),
        )

    def get_checkout_line_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: Decimal,
    ) -> Decimal:
        return previous_value

    def get_checkout_shipping_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: Decimal,
    ):
        return previous_value

    def _get_checkout_tax_data(
        self,
        checkout_info: "CheckoutInfo",
        lines_info: Iterable["CheckoutLineInfo"],
        discounts: Iterable[DiscountInfo],
        previous_value: Decimal,
    ):
        if self._skip_plugin(previous_value):
            return None

        valid = _validate_checkout(checkout_info, lines_info)
        if not valid:
            return None

        taxes_data = get_checkout_tax_data(
            checkout_info, lines_info, discounts, self.config
        )
        if not taxes_data or "error" in taxes_data:
            return None

        return taxes_data

    def _get_order_tax_data(
        self, order: "Order", previous_value: Union[Decimal, OrderTaxedPricesData]
    ):
        if self._skip_plugin(previous_value):
            return None

        valid = _validate_order(order)
        if not valid:
            return None

        taxes_data = get_order_tax_data(order, self.config, False)
        if not taxes_data or "error" in taxes_data:
            return None

        return taxes_data
