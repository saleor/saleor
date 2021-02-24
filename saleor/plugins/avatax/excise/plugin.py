import json
import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Iterable, Optional
from urllib.parse import urljoin

import opentracing
import opentracing.tags
from django.core.exceptions import ValidationError
from prices import Money, TaxedMoney

from ....checkout.models import Checkout
from ....core.prices import quantize_price
from ....core.taxes import TaxError, zero_taxed_money
from ....discount import DiscountInfo
from ...base_plugin import ConfigurationTypeField
from ...error_codes import PluginErrorCode
from .. import _validate_checkout
from ..plugin import AvataxPlugin
from . import (
    api_get_request,
    api_post_request,
    generate_request_data_from_checkout,
    get_api_url,
    get_checkout_tax_data,
    get_order_tax_data,
)

if TYPE_CHECKING:
    # flake8: noqa
    from ....account.models import Address
    from ....channel.models import Channel
    from ....checkout import CheckoutLineInfo
    from ....checkout.models import CheckoutLine
    from ....order.models import Order
    from ...models import PluginConfiguration

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
            "help_text": "Determines if Saleor should use Avatax Excise sandbox API.",
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
    }

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
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
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
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            logger.debug("Skip Plugin in Calculate Checkout Total")
            return previous_value
        checkout_total = previous_value

        if not _validate_checkout(checkout, [line_info.line for line_info in lines]):
            logger.debug("Checkout Invalid in Calculate Checkout Total")
            return checkout_total

        response = get_checkout_tax_data(checkout, discounts, self.config)
        if not response or "Errors found" in response["Status"]:
            return checkout_total

        if len(response["TransactionTaxes"]) == 0:
            raise TaxError("ATE did not return TransactionTaxes")

        currency = checkout.currency

        # store itemized tax information in Checkout metadata for optional display on the frontend
        # if there are no taxes, itemized taxes = []
        tax_item = {"itemized_taxes": json.dumps(response["TransactionTaxes"])}
        checkout_obj = Checkout.objects.filter(token=checkout.token).first()
        if checkout_obj:
            checkout_obj.store_value_in_metadata(items=tax_item)
            checkout_obj.save()

        tax = Money(Decimal(response.get("TotalTaxAmount", 0.0)), currency)
        net = checkout_total.net
        total_gross = net + tax
        taxed_total = quantize_price(TaxedMoney(net=net, gross=total_gross), currency)
        total = self._append_prices_of_not_taxed_lines(
            taxed_total, lines, checkout.channel, discounts
        )

        voucher_value = checkout.discount
        if voucher_value:
            total -= voucher_value

        return max(total, zero_taxed_money(total.currency))

    def calculate_checkout_subtotal(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        return previous_value

    def calculate_checkout_shipping(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        return previous_value

    def preprocess_order_creation(
        self,
        checkout: "Checkout",
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ):
        """Ensure all the data is correct and we can proceed with creation of order.

        Raise an error when can't receive taxes.
        """
        if self._skip_plugin(previous_value):
            return previous_value

        data = generate_request_data_from_checkout(
            checkout,
            transaction_type="RETAIL",
            discounts=discounts,
        )
        if not data.TransactionLines:
            return previous_value
        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox), "AvaTaxExcise/transactions/create"
        )
        with opentracing.global_tracer().start_active_span(
            "avatax_excise.transactions.create"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "tax")
            span.set_tag("service.name", "avatax_excise")
            response = api_post_request(transaction_url, data, self.config)
        if not response or response.get("Status") != "Success":
            transaction_errors = response.get("TransactionErrors")
            customer_msg = ""
            if isinstance(transaction_errors, list):
                for error in transaction_errors:
                    error_message = error.get("ErrorMessage")
                    if error_message:
                        customer_msg += error_message
                    error_code = response.get("ErrorCode", "")
                    logger.warning(
                        "Unable to calculate taxes for checkout %s, error_code: %s, "
                        "error_msg: %s",
                        checkout.token,
                        error_code,
                        error_message,
                    )
            raise TaxError(customer_msg)
        return previous_value

    def order_created(self, order: "Order", previous_value: Any) -> Any:

        # call the create transactions (similar flow as calculate checkout total)
        response = get_order_tax_data(order, self.config)

        # TODO handle error if get_order_tax_data fails

        transaction_id = response.get("UserTranId")

        if self.config.autocommit:
            # call the commit api with the UserTranId
            commit_url = urljoin(
                get_api_url(self.config.use_sandbox),
                f"AvaTaxExcise/transactions/{transaction_id}/commit",
            )
            commit_response = api_post_request(commit_url, None, self.config)

            # TODO do something if commit fails

        return previous_value

    def calculate_checkout_line_total(
        self,
        checkout: "Checkout",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        channel: "Channel",
        discounts: Iterable["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            # logger.debug("Skip plugin %s", previous_value)
            return previous_value

        base_total = previous_value
        if not checkout_line_info.product.charge_taxes:
            # logger.debug("Charge taxes is false for this item %s")
            return base_total

        if not _validate_checkout(checkout, [checkout_line_info.line]):
            # logger.debug("Checkout invalid %s")
            return base_total

        taxes_data = get_checkout_tax_data(checkout, discounts, self.config)

        if not taxes_data or "Error" in taxes_data["Status"]:
            logger.debug("Error in tax response %s")
            return base_total

        line_tax_total = Decimal(0)

        for line in taxes_data.get("TransactionTaxes", []):
            if line.get("InvoiceLine") == checkout_line_info.line.id:
                line_tax_total += Decimal(line.get("TaxAmount", 0.0))

        if not line_tax_total > 0:
            return base_total

        currency = checkout.currency
        tax = Decimal(line_tax_total)
        line_net = Decimal(base_total.net.amount)
        line_gross = Money(amount=line_net + tax, currency=currency)
        line_net = Money(amount=line_net, currency=currency)

        return quantize_price(TaxedMoney(net=line_net, gross=line_gross), currency)

    def calculate_checkout_line_unit_price(
        self,
        checkout: "Checkout",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        channel: "Channel",
        previous_value: TaxedMoney,
    ):
        return previous_value

    def get_checkout_line_tax_rate(
        self,
        checkout: "Checkout",
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: Decimal,
    ) -> Decimal:
        return previous_value

    def get_checkout_shipping_tax_rate(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: Decimal,
    ):
        return previous_value
