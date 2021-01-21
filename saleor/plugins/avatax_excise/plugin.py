import logging
import json
from dataclasses import asdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Union
from urllib.parse import urljoin
from ...checkout.models import Checkout, CheckoutLine

from django.core.exceptions import ValidationError
from django.conf import settings
from prices import Money, TaxedMoney, TaxedMoneyRange

from ...core.taxes import TaxError, TaxType, zero_taxed_money
from ...discount import DiscountInfo
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..error_codes import PluginErrorCode
from . import (
    META_CODE_KEY,
    META_DESCRIPTION_KEY,
    AvataxExciseConfiguration,
    CustomerErrors,
    TransactionType,
    _validate_checkout,
    _validate_order,
    api_post_request,
    generate_request_data_from_checkout,
    get_api_url,
    get_cached_tax_codes_or_fetch,
    get_checkout_tax_data,
    get_order_tax_data,
)
from .tasks import api_post_request_task

if TYPE_CHECKING:
    # flake8: noqa
    from ...checkout.models import Checkout, CheckoutLine
    from ...order.models import Order, OrderLine
    from ...product.models import Product, ProductType
    from ..models import PluginConfiguration


logger = logging.getLogger(__name__)


class AvataxExcisePlugin(BasePlugin):
    PLUGIN_NAME = "Avalara Excise"
    PLUGIN_ID = "mirumee.taxes.avalara_excise"

    DEFAULT_CONFIGURATION = [
        {"name": "Username or account", "value": None},
        {"name": "Password or license", "value": None},
        {"name": "Use sandbox", "value": False},
        {"name": "Company name", "value": "DEFAULT"},
        {"name": "Autocommit", "value": False},
    ]
    CONFIG_STRUCTURE = {
        "Username or account": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide user or account details",
            "label": "Username or account",
        },
        "Password or license": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide password or license details",
            "label": "Password or license",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should use Avalara Excise sandbox API.",
            "label": "Use sandbox",
        },
        "Company code": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Avalara Excise needs to receive company code. Some more "
            "complicated systems can use more than one company "
            "code, in that case, this variable should be changed "
            "based on data from Avalara Excise's admin panel",
            "label": "Company code",
        },
        "Autocommit": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines, if all transactions sent to Avalara Excise "
            "should be committed by default.",
            "label": "Autocommit",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = AvataxExciseConfiguration(
            username_or_account=configuration["Username or account"],
            password_or_license=configuration["Password or license"],
            use_sandbox=configuration["Use sandbox"],
            company_name=configuration["Company name"],
            autocommit=configuration["Autocommit"],
        )

    def _skip_plugin(self, previous_value: Union[TaxedMoney, TaxedMoneyRange]) -> bool:
        if not (self.config.username_or_account and self.config.password_or_license):
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

    def calculate_checkout_total(
        self,
        checkout: "Checkout",
        lines: Iterable["CheckoutLine"],
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        checkout_total = previous_value

        if not _validate_checkout(checkout):
            return checkout_total

        tax_response = get_checkout_tax_data(checkout, discounts, self.config)

        if not tax_response or "Error" in tax_response["Status"]:
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

        total_tax = Decimal(tax_response["TotalTaxAmount"])
        total_net = Decimal(checkout_total.net.amount)
        total_gross = Money(amount=total_net + total_tax, currency=currency)

        total_net = Money(amount=total_net, currency=currency)
        total = TaxedMoney(net=total_net, gross=total_gross)

        return max(total, zero_taxed_money(total.currency))

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

        if plugin_configuration.active and missing_fields:
            error_msg = (
                "To enable a plugin, you need to provide values for the "
                "following fields: "
            )
            raise ValidationError(
                error_msg + ", ".join(missing_fields),
                code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
            )
