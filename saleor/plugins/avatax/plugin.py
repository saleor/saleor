import logging
from collections.abc import Iterable
from dataclasses import asdict
from decimal import Decimal
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Optional, Union
from urllib.parse import urljoin

import opentracing
import opentracing.tags
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from django_countries import countries
from prices import Money, TaxedMoney, TaxedMoneyRange

from ...checkout import base_calculations
from ...checkout.fetch import fetch_checkout_lines
from ...checkout.utils import log_address_if_validation_skipped_for_checkout
from ...core.taxes import TaxError, TaxType, zero_taxed_money
from ...order import base_calculations as order_base_calculation
from ...order.interface import OrderTaxedPricesData
from ...product.models import ProductType
from ...tax import TaxCalculationStrategy
from ...tax.utils import (
    get_charge_taxes_for_checkout,
    get_charge_taxes_for_order,
    get_tax_app_identifier_for_checkout,
    get_tax_app_identifier_for_order,
    get_tax_calculation_strategy_for_checkout,
    get_tax_calculation_strategy_for_order,
)
from .. import PLUGIN_IDENTIFIER_PREFIX
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..error_codes import PluginErrorCode
from . import (
    DEFAULT_TAX_CODE,
    DEFAULT_TAX_DESCRIPTION,
    META_CODE_KEY,
    META_DESCRIPTION_KEY,
    AvataxConfiguration,
    CustomerErrors,
    TransactionType,
    _validate_checkout,
    _validate_order,
    api_get_request,
    api_post_request,
    generate_request_data_from_checkout,
    get_api_url,
    get_cached_tax_codes_or_fetch,
    get_checkout_tax_data,
    get_order_request_data,
    get_order_tax_data,
)
from .tasks import api_post_request_task

if TYPE_CHECKING:
    from ...account.models import Address
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...order.models import Order, OrderLine
    from ...product.models import Product, ProductVariant
    from ...tax.models import TaxClass
    from ..models import PluginConfiguration


logger = logging.getLogger(__name__)


def _get_prices_entered_with_tax_for_checkout(checkout_info: "CheckoutInfo"):
    tax_configuration = checkout_info.tax_configuration
    return tax_configuration.prices_entered_with_tax


def _get_prices_entered_with_tax_for_order(order: "Order"):
    tax_configuration = order.channel.tax_configuration
    return tax_configuration.prices_entered_with_tax


class AvataxPlugin(BasePlugin):
    PLUGIN_NAME = "Avalara"
    PLUGIN_ID = "mirumee.taxes.avalara"
    # identifier used in tax configuration
    PLUGIN_IDENTIFIER = PLUGIN_IDENTIFIER_PREFIX + PLUGIN_ID

    DEFAULT_CONFIGURATION = [
        {"name": "Username or account", "value": None},
        {"name": "Password or license", "value": None},
        {"name": "Use sandbox", "value": True},
        {"name": "Company name", "value": "DEFAULT"},
        {"name": "Autocommit", "value": False},
        {"name": "from_street_address", "value": None},
        {"name": "from_city", "value": None},
        {"name": "from_country", "value": None},
        {"name": "from_country_area", "value": None},
        {"name": "from_postal_code", "value": None},
        {"name": "shipping_tax_code", "value": "FR000000"},
    ]
    CONFIG_STRUCTURE = {
        "Username or account": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Provide user or account details",
            "label": "Username or account",
        },
        "Password or license": {
            "type": ConfigurationTypeField.PASSWORD,
            "help_text": "Provide password or license details",
            "label": "Password or license",
        },
        "Use sandbox": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines if Saleor should use Avatax sandbox API.",
            "label": "Use sandbox",
        },
        "Company name": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Avalara needs to receive company code. Some more "
            "complicated systems can use more than one company "
            "code, in that case, this variable should be changed "
            "based on data from Avalara's admin panel",
            "label": "Company name",
        },
        "Autocommit": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Determines, if all transactions sent to Avalara "
            "should be committed by default.",
            "label": "Autocommit",
        },
        "from_street_address": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "To calculate taxes we need to provide `ship from` details.",
            "label": "Ship from - street",
        },
        "from_city": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "To calculate taxes we need to provide `ship from` details.",
            "label": "Ship from - city",
        },
        "from_country": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "To calculate taxes we need to provide `ship from` details. "
            "Country code in ISO format. ",
            "label": "Ship from - country",
        },
        "from_country_area": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "To calculate taxes we need to provide `ship from` details.",
            "label": "Ship from - country area",
        },
        "from_postal_code": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "To calculate taxes we need to provide `ship from` details.",
            "label": "Ship from - postal code",
        },
        "shipping_tax_code": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Provide Avatax's tax code that will be included in the shipping line "
                "sent to Avatax."
            ),
            "label": "Shipping tax code",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}

        if from_country := configuration["from_country"]:
            from_country = countries.alpha2(from_country.strip())

        self.config = AvataxConfiguration(
            username_or_account=configuration["Username or account"],
            password_or_license=configuration["Password or license"],
            use_sandbox=configuration["Use sandbox"],
            company_name=configuration["Company name"],
            autocommit=configuration["Autocommit"],
            from_street_address=configuration["from_street_address"],
            from_city=configuration["from_city"],
            from_country=from_country,
            from_country_area=configuration["from_country_area"],
            from_postal_code=configuration["from_postal_code"],
            shipping_tax_code=configuration["shipping_tax_code"],
        )

    def _skip_plugin(
        self, previous_value: Union[TaxedMoney, TaxedMoneyRange, Decimal]
    ) -> bool:
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
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        response = self._get_checkout_tax_data(checkout_info, lines, previous_value)
        if response is None:
            return previous_value

        prices_entered_with_tax = partial(
            _get_prices_entered_with_tax_for_checkout, checkout_info
        )

        currency = checkout_info.checkout.currency
        taxed_total = zero_taxed_money(currency)

        for line in lines:
            taxed_line_total_data = self._calculate_checkout_line_total_price(
                taxes_data=response,
                item_code=line.variant.sku or line.variant.get_global_id(),
                prices_entered_with_tax=prices_entered_with_tax,
                # for some cases we will need a base_value but no need to call it for
                # each line
                base_value=SimpleLazyObject(
                    lambda: base_calculations.calculate_base_line_total_price(line)
                ),
            )
            taxed_total += taxed_line_total_data

        base_shipping_price = base_calculations.base_checkout_delivery_price(
            checkout_info, lines
        )
        shipping_price = self._calculate_checkout_shipping(
            checkout_info, currency, response.get("lines", []), base_shipping_price
        )

        taxed_total += shipping_price

        return max(
            taxed_total,
            zero_taxed_money(taxed_total.currency),
        )

    def _calculate_checkout_shipping(
        self,
        checkout_info: "CheckoutInfo",
        currency: str,
        lines: list[dict],
        shipping_price: Money,
    ) -> TaxedMoney:
        discount_amount = Decimal(0.0)
        shipping_tax = Decimal(0.0)
        shipping_net = shipping_price.amount
        for line in lines:
            if line["itemCode"] == "Shipping":
                # The lineAmount does not include the discountAmount,
                # but tax is calculated for discounted net price, that
                # take into account provided discount.
                shipping_net = Decimal(line["lineAmount"])
                discount_amount = Decimal(line.get("discountAmount", 0.0))
                shipping_tax = Decimal(line["tax"])
                break

        prices_entered_with_tax = partial(
            _get_prices_entered_with_tax_for_checkout, checkout_info
        )
        if currency == "JPY" and prices_entered_with_tax():
            shipping_gross = Money(amount=shipping_price.amount, currency=currency)
            shipping_net = Money(
                amount=shipping_gross.amount - shipping_tax, currency=currency
            )
        else:
            shipping_net -= discount_amount
            shipping_gross = Money(
                amount=shipping_net + shipping_tax, currency=currency
            )
            shipping_net = Money(amount=shipping_net, currency=currency)
        return TaxedMoney(net=shipping_net, gross=shipping_gross)

    def calculate_checkout_shipping(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        base_shipping_price = previous_value

        response = self._get_checkout_tax_data(checkout_info, lines, previous_value)
        if response is None:
            return previous_value

        currency = str(response.get("currencyCode"))
        return self._calculate_checkout_shipping(
            checkout_info, currency, response.get("lines", []), base_shipping_price.net
        )

    def preprocess_order_creation(
        self,
        checkout_info: "CheckoutInfo",
        lines: Optional[Iterable["CheckoutLineInfo"]],
        previous_value: Any,
    ):
        """Ensure all the data is correct and we can proceed with creation of order.

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

        tax_strategy = get_tax_calculation_strategy_for_checkout(checkout_info, lines)
        tax_app_identifier = get_tax_app_identifier_for_checkout(checkout_info, lines)
        if (
            tax_strategy == TaxCalculationStrategy.FLAT_RATES
            or tax_app_identifier is not None
            and tax_app_identifier != self.PLUGIN_IDENTIFIER
        ):
            return previous_value

        data = generate_request_data_from_checkout(
            checkout_info,
            lines,
            self.config,
            transaction_token=str(checkout_info.checkout.token),
            transaction_type=TransactionType.ORDER,
        )
        if not data.get("createTransactionModel", {}).get("lines"):
            return previous_value
        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox), "transactions/createoradjust"
        )
        with opentracing.global_tracer().start_active_span(
            "avatax.transactions.crateoradjust"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "tax")
            span.set_tag("service.name", "avatax")
            response = api_post_request(transaction_url, data, self.config)
        if not response or "error" in response:
            msg = response.get("error", {}).get("message", "")
            error_code = response.get("error", {}).get("code", "")
            logger.warning(
                "Unable to calculate taxes for checkout %s, error_code: %s, "
                "error_msg: %s",
                checkout_info.checkout.token,
                error_code,
                msg,
            )
            log_address_if_validation_skipped_for_checkout(checkout_info, logger)
            customer_msg = CustomerErrors.get_error_msg(response.get("error", {}))
            raise TaxError(customer_msg)
        return previous_value

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        tax_strategy = get_tax_calculation_strategy_for_order(order)
        tax_app_identifier = get_tax_app_identifier_for_order(order)
        if (
            tax_strategy == TaxCalculationStrategy.FLAT_RATES
            or tax_app_identifier is not None
            and tax_app_identifier != self.PLUGIN_IDENTIFIER
        ):
            return previous_value

        request_data = get_order_request_data(order, self.config)
        if not request_data:
            return previous_value

        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox), "transactions/createoradjust"
        )
        api_post_request_task.delay(
            transaction_url, request_data, asdict(self.config), order.id
        )
        return previous_value

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        charge_taxes = get_charge_taxes_for_checkout(checkout_info, lines)
        if not charge_taxes:
            return previous_value

        prices_entered_with_tax = partial(
            _get_prices_entered_with_tax_for_checkout, checkout_info
        )

        taxes_data = self._get_checkout_tax_data(checkout_info, lines, previous_value)
        variant = checkout_line_info.variant

        if not taxes_data or "error" in taxes_data:
            return previous_value

        return self._calculate_checkout_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            prices_entered_with_tax,
            base_value=SimpleLazyObject(
                lambda: base_calculations.calculate_base_line_total_price(
                    checkout_line_info
                )
            ),
        )

    @staticmethod
    def _calculate_checkout_line_total_price(
        taxes_data: dict[str, Any],
        item_code: str,
        prices_entered_with_tax: Callable[[], bool],
        # base_value should be provided as SimpleLazyObject
        base_value: Money,
    ) -> TaxedMoney:
        currency = taxes_data.get("currencyCode")

        for line in taxes_data.get("lines", []):
            if line.get("itemCode") != item_code:
                continue

            # The lineAmount does not include the discountAmount, but tax is calculated
            # for discounted net price, that take into account provided discount.
            tax = Decimal(line.get("tax", 0.0))
            discount_amount = Decimal(line.get("discountAmount", 0.0))
            net = Decimal(line["lineAmount"])

            if currency == "JPY" and prices_entered_with_tax():
                if isinstance(base_value, SimpleLazyObject):
                    base_value = base_value._setupfunc()  # type: ignore

                line_gross = Money(
                    base_value.amount - discount_amount, currency=currency
                )
                line_net = Money(amount=line_gross.amount - tax, currency=currency)
            else:
                net -= discount_amount
                line_gross = Money(amount=net + tax, currency=currency)
                line_net = Money(amount=net, currency=currency)

            return TaxedMoney(net=line_net, gross=line_gross)
        if isinstance(base_value, SimpleLazyObject):
            base_value = base_value._setupfunc()  # type: ignore
        return TaxedMoney(net=base_value, gross=base_value)

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

        charge_taxes = get_charge_taxes_for_order(order)
        if not charge_taxes:
            return previous_value

        base_value = order_base_calculation.base_order_line_total(order_line)

        prices_entered_with_tax = partial(_get_prices_entered_with_tax_for_order, order)
        taxes_data = self._get_order_tax_data(order, previous_value)
        return self._calculate_order_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            prices_entered_with_tax,
            base_value,
        )

    @staticmethod
    def _calculate_order_line_total_price(
        taxes_data: dict[str, Any],
        item_code: str,
        prices_entered_with_tax: Callable[[], bool],
        base_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        if not taxes_data or "error" in taxes_data:
            return base_value

        currency = taxes_data.get("currencyCode")
        line_price_with_discounts = None

        for line in taxes_data.get("lines", []):
            if line.get("itemCode") != item_code:
                continue

            # The lineAmount does not include the discountAmount, but tax is calculated
            # for discounted net price, that take into account provided discount.
            tax = Decimal(line.get("tax", 0.0))
            discount_amount = Decimal(line.get("discountAmount", 0.0))
            net = Decimal(line["lineAmount"])

            if currency == "JPY" and prices_entered_with_tax():
                line_gross = Money(
                    base_value.price_with_discounts.gross.amount - discount_amount,
                    currency,
                )
                line_net = Money(amount=line_gross.amount - tax, currency=currency)
            else:
                net -= discount_amount
                line_gross = Money(amount=net + tax, currency=currency)
                line_net = Money(amount=net, currency=currency)

            line_price_with_discounts = TaxedMoney(net=line_net, gross=line_gross)

        if line_price_with_discounts is not None:
            return OrderTaxedPricesData(
                undiscounted_price=base_value.undiscounted_price,
                price_with_discounts=line_price_with_discounts,
            )

        return base_value

    def calculate_checkout_line_unit_price(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        base_total = previous_value
        charge_taxes = get_charge_taxes_for_checkout(checkout_info, lines)

        if not charge_taxes:
            return base_total

        prices_entered_with_tax = partial(
            _get_prices_entered_with_tax_for_checkout, checkout_info
        )
        variant = checkout_line_info.variant

        quantity = checkout_line_info.line.quantity
        taxes_data = self._get_checkout_tax_data(checkout_info, lines, previous_value)
        if not taxes_data or "error" in taxes_data:
            return previous_value

        taxed_total_price = self._calculate_checkout_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            prices_entered_with_tax,
            base_value=SimpleLazyObject(
                lambda: base_calculations.calculate_base_line_total_price(
                    checkout_line_info
                )
            ),
        )
        return taxed_total_price / quantity

    def calculate_order_line_unit(
        self,
        order: "Order",
        order_line: "OrderLine",
        variant: "ProductVariant",
        product: "Product",
        previous_value: OrderTaxedPricesData,
    ) -> OrderTaxedPricesData:
        charge_taxes = get_charge_taxes_for_order(order)
        if not variant or (variant and not charge_taxes):
            return previous_value

        prices_entered_with_tax = partial(_get_prices_entered_with_tax_for_order, order)

        quantity = order_line.quantity
        taxes_data = self._get_order_tax_data(order, previous_value)

        base_total = order_base_calculation.base_order_line_total(order_line)

        taxed_total_prices_data = self._calculate_order_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            prices_entered_with_tax,
            base_total,
        )
        return OrderTaxedPricesData(
            undiscounted_price=taxed_total_prices_data.undiscounted_price / quantity,
            price_with_discounts=taxed_total_prices_data.price_with_discounts
            / quantity,
        )

    def _calculate_order_shipping(self, order, taxes_data) -> TaxedMoney:
        prices_entered_with_tax = partial(_get_prices_entered_with_tax_for_order, order)
        currency = taxes_data.get("currencyCode")
        for line in taxes_data.get("lines", []):
            if line["itemCode"] == "Shipping":
                tax = Decimal(line.get("tax", 0.0))
                discount_amount = Decimal(line.get("discountAmount", 0.0))
                net = Decimal(line.get("lineAmount", 0.0)) - discount_amount
                if currency == "JPY" and prices_entered_with_tax():
                    gross = order.base_shipping_price
                    net = Money(amount=gross.amount - tax, currency=currency)
                else:
                    gross = Money(amount=net + tax, currency=currency)
                    net = Money(amount=net, currency=currency)
                return TaxedMoney(net=net, gross=gross)

        price = order.base_shipping_price
        return TaxedMoney(
            net=price,
            gross=price,
        )

    def calculate_order_shipping(
        self, order: "Order", previous_value: TaxedMoney
    ) -> TaxedMoney:
        taxes_data = self._get_order_tax_data(order, previous_value)
        if taxes_data is None:
            return previous_value
        return self._calculate_order_shipping(order, taxes_data)

    def calculate_order_total(
        self,
        order: "Order",
        lines: Iterable["OrderLine"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        taxes_data = self._get_order_tax_data(order, previous_value)
        prices_entered_with_tax = partial(_get_prices_entered_with_tax_for_order, order)

        currency = order.currency
        taxed_subtotal = zero_taxed_money(currency)

        for line in lines:
            base_line_price = OrderTaxedPricesData(
                undiscounted_price=line.undiscounted_base_unit_price * line.quantity,
                price_with_discounts=TaxedMoney(
                    line.base_unit_price, line.base_unit_price
                )
                * line.quantity,
            )
            taxed_line_total_data = self._calculate_order_line_total_price(
                taxes_data,
                line.product_sku or line.variant_name,
                prices_entered_with_tax,
                base_line_price,
            ).price_with_discounts
            taxed_subtotal += taxed_line_total_data

        shipping_price = order.base_shipping_price
        if taxes_data is not None:
            shipping_price = self._calculate_order_shipping(order, taxes_data)

        taxed_total = taxed_subtotal + shipping_price

        return max(
            taxed_total,
            zero_taxed_money(currency),
        )

    def get_tax_rate_type_choices(self, previous_value: Any) -> list[TaxType]:
        if not self.active:
            return previous_value
        return [
            TaxType(code=tax_code, description=desc)
            for tax_code, desc in get_cached_tax_codes_or_fetch(self.config).items()
        ]

    def get_checkout_line_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        previous_value: Decimal,
    ) -> Decimal:
        charge_taxes = get_charge_taxes_for_checkout(checkout_info, lines)
        if not charge_taxes:
            return previous_value

        response = self._get_checkout_tax_data(checkout_info, lines, previous_value)
        variant = checkout_line_info.variant
        return self._get_unit_tax_rate(
            response,
            variant.sku or variant.get_global_id(),
            previous_value,
        )

    def get_order_line_tax_rate(
        self,
        order: "Order",
        product: "Product",
        variant: "ProductVariant",
        address: Optional["Address"],
        previous_value: Decimal,
    ) -> Decimal:
        charge_taxes = get_charge_taxes_for_order(order)
        if not charge_taxes:
            return previous_value

        response = self._get_order_tax_data(order, previous_value)
        return self._get_unit_tax_rate(
            response,
            variant.sku or variant.get_global_id(),
            previous_value,
        )

    def get_checkout_shipping_tax_rate(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        address: Optional["Address"],
        previous_value: Decimal,
    ):
        response = self._get_checkout_tax_data(checkout_info, lines, previous_value)
        return self._get_shipping_tax_rate(response, previous_value)

    def get_order_shipping_tax_rate(self, order: "Order", previous_value: Decimal):
        response = self._get_order_tax_data(order, previous_value)
        return self._get_shipping_tax_rate(response, previous_value)

    def _get_checkout_tax_data(
        self,
        checkout_info: "CheckoutInfo",
        lines_info: Iterable["CheckoutLineInfo"],
        base_value: Union[TaxedMoney, Decimal],
    ):
        if self._skip_plugin(base_value):
            self._set_checkout_tax_error(checkout_info, lines_info)
            return None

        valid = _validate_checkout(checkout_info, lines_info)
        if not valid:
            self._set_checkout_tax_error(checkout_info, lines_info)
            return None

        response = get_checkout_tax_data(checkout_info, lines_info, self.config)

        if not response or "error" in response:
            self._set_checkout_tax_error(checkout_info, lines_info)
            return None

        return response

    def _set_checkout_tax_error(
        self,
        checkout_info: "CheckoutInfo",
        lines_info: Iterable["CheckoutLineInfo"],
    ) -> None:
        app_identifier = get_tax_app_identifier_for_checkout(checkout_info, lines_info)
        if app_identifier == self.PLUGIN_IDENTIFIER:
            checkout_info.checkout.tax_error = "Empty tax data."

    def _get_order_tax_data(
        self, order: "Order", base_value: Union[Decimal, OrderTaxedPricesData]
    ):
        if self._skip_plugin(base_value):
            self._set_order_tax_error(order)
            return None

        valid = _validate_order(order)
        if not valid:
            self._set_order_tax_error(order)
            return None

        response = get_order_tax_data(order, self.config, False)
        if not response or "error" in response:
            self._set_order_tax_error(order)
            return None

        return response

    def _set_order_tax_error(self, order: "Order") -> None:
        app_identifier = get_tax_app_identifier_for_order(order)
        if app_identifier == self.PLUGIN_IDENTIFIER:
            order.tax_error = "Empty tax data."

    @staticmethod
    def _get_unit_tax_rate(
        response: dict[str, Any],
        item_code: str,
        base_rate: Decimal,
    ):
        if response is None:
            return base_rate
        lines_data = response.get("lines", [])
        for line in lines_data:
            if line["itemCode"] == item_code:
                details = line.get("details")
                if not details:
                    return base_rate
                # when tax is equal to 0 tax rate for product is still provided
                # in the response
                tax = Decimal(sum([detail.get("tax", 0.0) for detail in details]))
                rate = Decimal(sum([detail.get("rate", 0.0) for detail in details]))
                return rate if tax != Decimal(0.0) else base_rate
        return base_rate

    @staticmethod
    def _get_shipping_tax_rate(
        response: dict[str, Any],
        base_rate: Decimal,
    ):
        if response is None:
            return base_rate
        lines_data = response.get("lines", [])
        for line in lines_data:
            if line["itemCode"] == "Shipping":
                line_details = line.get("details")
                if not line_details:
                    return base_rate
                return sum(
                    [Decimal(detail.get("rate", 0.0)) for detail in line_details]
                )
        return base_rate

    def get_tax_code_from_object_meta(
        self,
        obj: Union["Product", "ProductType", "TaxClass"],
        previous_value: Any,
    ) -> TaxType:
        if not self.active:
            return previous_value

        # Product has None as it determines if we overwrite taxes for the product
        default_tax_code = None
        default_tax_description = None
        if isinstance(obj, ProductType):
            default_tax_code = DEFAULT_TAX_CODE
            default_tax_description = DEFAULT_TAX_DESCRIPTION

        tax_code = obj.get_value_from_metadata(META_CODE_KEY, default_tax_code)
        tax_description = obj.get_value_from_metadata(
            META_DESCRIPTION_KEY, default_tax_description
        )
        return TaxType(
            code=tax_code,
            description=tax_description,
        )

    @classmethod
    def validate_authentication(cls, plugin_configuration: "PluginConfiguration"):
        conf = {
            data["name"]: data["value"] for data in plugin_configuration.configuration
        }
        url = urljoin(get_api_url(conf["Use sandbox"]), "utilities/ping")
        with opentracing.global_tracer().start_active_span(
            "avatax.utilities.ping"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "tax")
            span.set_tag("service.name", "avatax")
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

        required_from_address_fields = [
            "from_street_address",
            "from_city",
            "from_country",
            "from_postal_code",
        ]

        all_address_fields = all(
            [configuration[field] for field in required_from_address_fields]
        )
        if not all_address_fields:
            missing_fields.extend(required_from_address_fields)

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
