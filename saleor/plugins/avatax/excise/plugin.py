import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable, Optional, Union
from urllib.parse import urljoin

import opentracing
import opentracing.tags
from django.core.exceptions import ValidationError
from prices import Money, TaxedMoney, TaxedMoneyRange

from ....checkout.models import Checkout
from ....core.taxes import TaxError, TaxType, charge_taxes_on_shipping, zero_taxed_money
from ....discount import DiscountInfo
from ...base_plugin import BasePlugin, ConfigurationTypeField
from ...error_codes import PluginErrorCode
from .. import _validate_checkout
from . import api_get_request, api_post_request, get_api_url, get_checkout_tax_data

# from ....checkout.models import Checkout


logger = logging.getLogger(__name__)


@dataclass
class AvataxConfiguration:
    username: str
    password: str
    use_sandbox: bool = True
    company_id: str = None


class AvataxExcisePlugin(BasePlugin):
    PLUGIN_NAME = "Avalara Excise"
    PLUGIN_ID = "mirumee.taxes.avalara_excise"

    DEFAULT_CONFIGURATION = [
        {"name": "Username", "value": None},
        {"name": "Password", "value": None},
        {"name": "Use sandbox", "value": True},
        {"name": "Company ID", "value": None},
    ]
    CONFIG_STRUCTURE = {
        "Username": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide user details",
            "label": "Username",
        },
        "Password": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": "Provide password details",
            "label": "Password",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should use Avatax Excise sandbox API.",
            "label": "Use sandbox",
        },
        "Company ID": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Avalara company ID.",
            "label": "Company ID",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = AvataxConfiguration(
            username=configuration["Username"],
            password=configuration["Password"],
            use_sandbox=configuration["Use sandbox"],
            company_id=configuration["Company ID"],
        )

    def _skip_plugin(
        self, previous_value: Union[TaxedMoney, TaxedMoneyRange, Decimal]
    ) -> bool:
        if not (self.config.username and self.config.password):
            return True

        if not self.active:
            return True

        # The previous plugin already calculated taxes so we can skip our logic
        if isinstance(previous_value, TaxedMoneyRange):
            start = previous_value.start
            stop = previous_value.stop

            return start.net != start.gross and stop.net != stop.gross

        if isinstance(previous_value, TaxedMoney):
            return previous_value.net != previous_value.gross
        return False

    @classmethod
    def validate_authentication(cls, plugin_configuration: "PluginConfiguration"):
        conf = {
            data["name"]: data["value"] for data in plugin_configuration.configuration
        }
        url = urljoin(get_api_url(conf["Use sandbox"]), "utilities/ping")
        response = api_get_request(
            url,
            username_or_account=conf["Username"],
            password_or_license=conf["Password"],
        )

        if not response.get("authenticated"):
            raise ValidationError(
                "Authentication failed. Please check provided data.",
                code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
            )

    def calculate_checkout_total(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLine"],
        address: Optional["Address"],
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            logger.debug("Skip plugin %s", previous_value)
            return previous_value

        checkout_total = previous_value

        if not _validate_checkout(checkout, [line_info.line for line_info in lines]):
            logger.debug("Checkout invalid %s")
            return checkout_total

        # tax_response = get_checkout_tax_data(checkout, discounts, self.config)
        tax_response = {
            "UserTranId": "e00ef935-79b2-48d9-b671-33c36bd58444",
            "TranId": 38546949,
            "Status": "Success",
            "ReturnCode": 0,
            "TotalTaxAmount": 60.21,
            "TransactionTaxes": [
                {
                    "TransactionTaxAmounts": [],
                    "SequenceId": 1,
                    "TransactionLine": 1,
                    "InvoiceLine": 220,
                    "CountryCode": "USA",
                    "Jurisdiction": "TX",
                    "LocalJurisdiction": "48",
                    "ProductCategory": 0.0,
                    "TaxingLevel": "STA",
                    "TaxType": "S",
                    "RateType": "G",
                    "RateSubtype": "NONE",
                    "CalculationTypeInd": "P",
                    "TaxRate": 0.062500,
                    "TaxQuantity": 0.0,
                    "TaxAmount": 45.61,
                    "TaxExemptionInd": "N",
                    "SalesTaxBaseAmount": 729.7900,
                    "LicenseNumber": "",
                    "RateDescription": "TX STATE TAX - TEXAS",
                    "Currency": "USD",
                    "SubtotalInd": "C",
                    "StatusCode": "ACTIVE",
                    "QuantityInd": "B",
                },
                {
                    "TransactionTaxAmounts": [],
                    "SequenceId": 2,
                    "TransactionLine": 1,
                    "InvoiceLine": 220,
                    "CountryCode": "USA",
                    "Jurisdiction": "TX",
                    "LocalJurisdiction": "19000",
                    "ProductCategory": 0.0,
                    "TaxingLevel": "CIT",
                    "TaxType": "S",
                    "RateType": "G",
                    "RateSubtype": "NONE",
                    "CalculationTypeInd": "P",
                    "TaxRate": 0.010000,
                    "TaxQuantity": 0.0,
                    "TaxAmount": 7.30,
                    "TaxExemptionInd": "N",
                    "SalesTaxBaseAmount": 729.7900,
                    "LicenseNumber": "",
                    "RateDescription": "TX CITY TAX - DALLAS",
                    "Currency": "USD",
                    "SubtotalInd": "C",
                    "StatusCode": "ACTIVE",
                    "QuantityInd": "B",
                },
                {
                    "TransactionTaxAmounts": [],
                    "SequenceId": 3,
                    "TransactionLine": 1,
                    "InvoiceLine": 220,
                    "CountryCode": "USA",
                    "Jurisdiction": "TX",
                    "LocalJurisdiction": "6000816",
                    "ProductCategory": 0.0,
                    "TaxingLevel": "STJ",
                    "TaxType": "S",
                    "RateType": "G",
                    "RateSubtype": "NONE",
                    "CalculationTypeInd": "P",
                    "TaxRate": 0.010000,
                    "TaxQuantity": 0.0,
                    "TaxAmount": 7.30,
                    "TaxExemptionInd": "N",
                    "SalesTaxBaseAmount": 729.7900,
                    "LicenseNumber": "",
                    "RateDescription": "TX SPECIAL TAX - DALLAS MTA TRANSIT",
                    "Currency": "USD",
                    "SubtotalInd": "C",
                    "StatusCode": "ACTIVE",
                    "QuantityInd": "B",
                },
            ],
            "TransactionErrors": [],
            "UserReturnValue": "",
        }

        if not tax_response or "Error" in tax_response["Status"]:
            logger.debug("Error in tax response %s")
            return checkout_total

        # store itemized tax information in Checkout metadata for optional display on the frontend
        # if there are no taxes, itemized taxes = []

        tax_item = {"itemized_taxes": tax_response["TransactionTaxes"]}
        checkout_obj = Checkout.objects.filter(token=checkout.token).first()
        checkout_obj.store_value_in_metadata(items=tax_item)
        checkout_obj.save()

        # currency is stored on individual tax lines in TransactionTaxes
        # if there are tax lines we take the currency of the first one, assuming they are all the same

        if tax_response["TransactionTaxes"][0]:
            currency = tax_response["TransactionTaxes"][0]["Currency"]
        else:
            currency = settings.DEFAULT_CURRENCY

        tax = Money(tax_response.get("TotalTaxAmount", 0.0), currency)
        pre_tax = checkout_total.net
        total_gross = pre_tax + tax
        taxed_total = TaxedMoney(net=pre_tax, gross=total_gross)
        total = self._append_prices_of_not_taxed_lines(
            taxed_total, lines, checkout.channel, discounts
        )

        voucher_value = checkout.discount
        if voucher_value:
            total -= voucher_value

        return max(total, zero_taxed_money(total.currency))

    def calculate_checkout_line_total(
        self,
        checkout: "Checkout",
        checkout_line: "CheckoutLine",
        variant: "ProductVariant",
        product: "Product",
        collections: Iterable["Collection"],
        address: Optional["Address"],
        channel: "Channel",
        channel_listing: "ProductVariantChannelListing",
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        base_total = previous_value
        if not checkout_line.variant.product.charge_taxes:
            return base_total

        if not _validate_checkout(checkout, [checkout_line]):
            logger.debug("Checkout not valid %s")
            return base_total

        taxes_data = get_checkout_tax_data(checkout, discounts, self.config)
        print("ZOOT checkout line function firing")
        if not taxes_data or "Error" in taxes_data["Status"]:
            logger.debug("Error in tax response %s")
            return checkout_total

        currency = taxes_data.get("currencyCode")

        for line in taxes_data.get("lines", []):
            if line.get("itemCode") == variant.sku:
                tax = Decimal(line.get("tax", 0.0))
                line_net = Decimal(line["lineAmount"])
                line_gross = Money(amount=line_net + tax, currency=currency)
                line_net = Money(amount=line_net, currency=currency)
                return TaxedMoney(net=line_net, gross=line_gross)

        return base_total

    # this is copied from regular avalara as i was having a problem importing it
    # should probably figure out why
    def _append_prices_of_not_taxed_lines(
        self,
        price: TaxedMoney,
        lines: Iterable["CheckoutLineInfo"],
        channel: "Channel",
        discounts: Iterable[DiscountInfo],
    ):
        for line_info in lines:
            if line_info.variant.product.charge_taxes:
                continue
            line_price = base_calculations.base_checkout_line_total(
                line_info.line,
                line_info.variant,
                line_info.product,
                line_info.collections,
                channel,
                line_info.channel_listing,
                discounts,
            )
            price.gross.amount += line_price.gross.amount
            price.net.amount += line_price.net.amount
        return price
