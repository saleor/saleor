import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Union
from urllib.parse import urljoin

from django.conf import settings
from django.utils.translation import pgettext_lazy
from prices import Money, TaxedMoney, TaxedMoneyRange

from ....core.taxes import TaxError, TaxType, zero_taxed_money
from ... import ConfigurationTypeField
from ...base_plugin import BasePlugin
from . import (
    META_FIELD,
    META_NAMESPACE,
    AvataxConfiguration,
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
    from ....checkout.models import Checkout, CheckoutLine
    from ....order.models import Order, OrderLine

logger = logging.getLogger(__name__)


class AvataxPlugin(BasePlugin):
    PLUGIN_NAME = "Avalara"
    CONFIG_STRUCTURE = {
        "Username or account": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide user or account details"
            ),
            "label": pgettext_lazy("Plugin label", "Username or account"),
        },
        "Password or license": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text", "Provide password or license details"
            ),
            "label": pgettext_lazy("Plugin label", "Password or license"),
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines if Saleor should use Avatax sandbox API.",
            ),
            "label": pgettext_lazy("Plugin label", "Use sandbox"),
        },
        "Company name": {
            "type": ConfigurationTypeField.STRING,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Avalara needs to receive company code. Some more "
                "complicated systems can use more than one company "
                "code, in that case, this variable should be changed "
                "based on data from Avalara's admin panel",
            ),
            "label": pgettext_lazy("Plugin label", "Company name"),
        },
        "Autocommit": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": pgettext_lazy(
                "Plugin help text",
                "Determines, if all transactions sent to Avalara "
                "should be committed by default.",
            ),
            "label": pgettext_lazy("Plugin label", "Autocommit"),
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None

    def _initialize_plugin_configuration(self):
        super()._initialize_plugin_configuration()

        if self._cached_config and self._cached_config.configuration:
            configuration = self._cached_config.configuration

            # Convert to dict to easier take config elements
            configuration = {item["name"]: item["value"] for item in configuration}
            self.config = AvataxConfiguration(
                username_or_account=configuration["Username or account"],
                password_or_license=configuration["Password or license"],
                use_sandbox=configuration["Use sandbox"] == "true",
                company_name=configuration["Company name"],
                autocommit=configuration["Autocommit"] == "true",
            )
        else:
            # This should be removed after we drop an Avatax's settings from Django
            # settings file
            self.config = AvataxConfiguration(
                username_or_account=settings.AVATAX_USERNAME_OR_ACCOUNT,
                password_or_license=settings.AVATAX_PASSWORD_OR_LICENSE,
                use_sandbox=settings.AVATAX_USE_SANDBOX,
                autocommit=settings.AVATAX_AUTOCOMMIT,
                company_name=settings.AVATAX_COMPANY_NAME,
            )
            self.active = (
                settings.AVATAX_USERNAME_OR_ACCOUNT
                and settings.AVATAX_PASSWORD_OR_LICENSE
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
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        checkout_total = checkout.get_total(discounts=discounts)
        if not _validate_checkout(checkout):
            return TaxedMoney(net=checkout_total, gross=checkout_total)
        response = get_checkout_tax_data(checkout, discounts, self.config)
        if not response or "error" in response:
            return TaxedMoney(net=checkout_total, gross=checkout_total)

        currency = response.get("currencyCode")
        tax = Decimal(response.get("totalTax", 0.0))
        total_net = Decimal(response.get("totalAmount", 0.0))
        total_gross = Money(amount=total_net + tax, currency=currency)
        total_net = Money(amount=total_net, currency=currency)
        total = TaxedMoney(net=total_net, gross=total_gross)
        voucher_amount = checkout.discount_amount
        if voucher_amount:
            total -= voucher_amount
        return max(total, zero_taxed_money(total.currency))

    def _calculate_checkout_subtotal(
        self, currency: str, lines: List[Dict]
    ) -> TaxedMoney:
        sub_tax = Decimal(0.0)
        sub_net = Decimal(0.0)
        for line in lines:
            if line["itemCode"] == "Shipping":
                continue
            sub_tax += Decimal(line["tax"])
            sub_net += Decimal(line.get("lineAmount", 0.0))
        sub_total_gross = Money(sub_net + sub_tax, currency)
        sub_total_net = Money(sub_net, currency)
        return TaxedMoney(net=sub_total_net, gross=sub_total_gross)

    def calculate_checkout_subtotal(
        self,
        checkout: "Checkout",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        sub_total = checkout.get_subtotal(discounts)
        if not _validate_checkout(checkout):
            return TaxedMoney(net=sub_total, gross=sub_total)

        response = get_checkout_tax_data(checkout, discounts, self.config)
        if not response or "error" in response:
            return TaxedMoney(net=sub_total, gross=sub_total)

        currency = response.get("currencyCode")
        return self._calculate_checkout_subtotal(currency, response.get("lines", []))

    def _calculate_checkout_shipping(
        self, currency: str, lines: List[Dict], shipping_price: Money
    ) -> TaxedMoney:
        shipping_tax = Decimal(0.0)
        shipping_net = shipping_price.amount
        for line in lines:
            if line["itemCode"] == "Shipping":
                shipping_net = Decimal(line["lineAmount"])
                shipping_tax = Decimal(line["tax"])
                break

        shipping_gross = Money(amount=shipping_net + shipping_tax, currency=currency)
        shipping_net = Money(amount=shipping_net, currency=currency)
        return TaxedMoney(net=shipping_net, gross=shipping_gross)

    def calculate_checkout_shipping(
        self,
        checkout: "Checkout",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        shipping_price = checkout.get_shipping_price()
        if not _validate_checkout(checkout):
            return TaxedMoney(net=shipping_price, gross=shipping_price)

        response = get_checkout_tax_data(checkout, discounts, self.config)
        if not response or "error" in response:
            return TaxedMoney(net=shipping_price, gross=shipping_price)

        currency = response.get("currencyCode")
        return self._calculate_checkout_shipping(
            currency, response.get("lines", []), shipping_price
        )

    def preprocess_order_creation(
        self, checkout: "Checkout", discounts: List["DiscountInfo"], previous_value: Any
    ):
        """Ensure all the data is correct and we can proceed with creation of order.

        Raise an error when can't receive taxes.
        """
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        data = generate_request_data_from_checkout(
            checkout,
            self.config,
            transaction_token=str(checkout.token),
            transaction_type=TransactionType.ORDER,
            discounts=discounts,
        )
        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox), "transactions/createoradjust"
        )
        response = api_post_request(transaction_url, data, self.config)
        if not response or "error" in response:
            msg = response.get("error", {}).get("message", "")
            error_code = response.get("error", {}).get("code", "")
            logger.warning(
                "Unable to calculate taxes for checkout %s, error_code: %s, "
                "error_msg: %s",
                checkout.token,
                error_code,
                msg,
            )
            customer_msg = CustomerErrors.get_error_msg(response.get("error", {}))
            raise TaxError(customer_msg)
        return previous_value

    def postprocess_order_creation(self, order: "Order", previous_value: Any) -> Any:
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value
        data = get_order_tax_data(order, self.config, force_refresh=True)

        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox), "transactions/createoradjust"
        )
        api_post_request_task.delay(transaction_url, data)
        return previous_value

    def calculate_checkout_line_total(
        self,
        checkout_line: "CheckoutLine",
        discounts: List["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        checkout = checkout_line.checkout
        total = checkout_line.get_total(discounts)
        if not _validate_checkout(checkout):
            return TaxedMoney(net=total, gross=total)
        taxes_data = get_checkout_tax_data(checkout, discounts, self.config)
        currency = taxes_data.get("currencyCode")
        for line in taxes_data.get("lines", []):
            if line.get("itemCode") == checkout_line.variant.sku:
                tax = Decimal(line.get("tax", 0.0))
                line_net = Decimal(line["lineAmount"])
                line_gross = Money(amount=line_net + tax, currency=currency)
                line_net = Money(amount=line_net, currency=currency)
                return TaxedMoney(net=line_net, gross=line_gross)

        total = checkout_line.get_total(discounts)
        return TaxedMoney(net=total, gross=total)

    def _calculate_order_line_unit(self, order_line):
        order = order_line.order
        taxes_data = get_order_tax_data(order, self.config)
        currency = taxes_data.get("currencyCode")
        for line in taxes_data.get("lines", []):
            if line.get("itemCode") == order_line.variant.sku:
                tax = Decimal(line.get("tax", 0.0)) / order_line.quantity
                net = Decimal(line.get("lineAmount", 0.0)) / order_line.quantity

                gross = Money(amount=net + tax, currency=currency)
                net = Money(amount=net, currency=currency)
                return TaxedMoney(net=net, gross=gross)

    def calculate_order_line_unit(
        self, order_line: "OrderLine", previous_value: TaxedMoney
    ) -> TaxedMoney:
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        if _validate_order(order_line.order):
            return self._calculate_order_line_unit(order_line)
        return order_line.unit_price

    def calculate_order_shipping(
        self, order: "Order", previous_value: TaxedMoney
    ) -> TaxedMoney:
        self._initialize_plugin_configuration()

        if self._skip_plugin(previous_value):
            return previous_value

        if not _validate_order(order):
            return zero_taxed_money(order.total.currency)
        taxes_data = get_order_tax_data(order, self.config, False)
        currency = taxes_data.get("currencyCode")
        for line in taxes_data.get("lines", []):
            if line["itemCode"] == "Shipping":
                tax = Decimal(line.get("tax", 0.0))
                net = Decimal(line.get("lineAmount", 0.0))
                gross = Money(amount=net + tax, currency=currency)
                net = Money(amount=net, currency=currency)
                return TaxedMoney(net=net, gross=gross)
        return TaxedMoney(
            net=order.shipping_method.price, gross=order.shipping_method.price
        )

    def get_tax_rate_type_choices(self, previous_value: Any) -> List[TaxType]:
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value
        return [
            TaxType(code=tax_code, description=desc)
            for tax_code, desc in get_cached_tax_codes_or_fetch(self.config).items()
        ]

    def assign_tax_code_to_object_meta(
        self, obj: Union["Product", "ProductType"], tax_code: str, previous_value: Any
    ):
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value

        codes = get_cached_tax_codes_or_fetch(self.config)
        if tax_code not in codes:
            return

        tax_description = codes[tax_code]
        tax_item = {"code": tax_code, "description": tax_description}
        stored_tax_meta = obj.get_meta(namespace=META_NAMESPACE, client=META_FIELD)
        stored_tax_meta.update(tax_item)
        obj.store_meta(
            namespace=META_NAMESPACE, client=META_FIELD, item=stored_tax_meta
        )
        obj.save()

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"], previous_value: Any
    ) -> TaxType:
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value
        tax = obj.get_meta(namespace=META_NAMESPACE, client=META_FIELD)
        return TaxType(code=tax.get("code", ""), description=tax.get("description", ""))

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value
        return False

    def taxes_are_enabled(self, previous_value: bool) -> bool:
        self._initialize_plugin_configuration()

        if not self.active:
            return previous_value
        return True

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": False,
            "configuration": [
                {"name": "Username or account", "value": ""},
                {"name": "Password or license", "value": ""},
                {"name": "Use sandbox", "value": True},
                {"name": "Company name", "value": "DEFAULT"},
                {"name": "Autocommit", "value": False},
            ],
        }
        return defaults
