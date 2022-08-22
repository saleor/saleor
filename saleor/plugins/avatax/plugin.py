import logging
from dataclasses import asdict
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Union
from urllib.parse import urljoin

import opentracing
import opentracing.tags
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.utils.functional import SimpleLazyObject
from django_countries import countries
from prices import Money, TaxedMoney, TaxedMoneyRange

from ...checkout import base_calculations
from ...checkout.fetch import fetch_checkout_lines
from ...core.taxes import TaxError, TaxType, charge_taxes_on_shipping, zero_taxed_money
from ...discount import DiscountInfo
from ...order.interface import OrderTaxedPricesData
from ...product.models import ProductType
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
    # flake8: noqa
    from ...account.models import Address
    from ...channel.models import Channel
    from ...checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ...checkout.models import Checkout, CheckoutLine
    from ...order.models import Order, OrderLine
    from ...product.models import Product, ProductVariant
    from ..models import PluginConfiguration


logger = logging.getLogger(__name__)


class AvataxPlugin(BasePlugin):
    PLUGIN_NAME = "Avalara"
    PLUGIN_ID = "mirumee.taxes.avalara"

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
        {"name": "override_global_tax", "value": False},
        {"name": "include_taxes_in_prices", "value": True},
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
        "override_global_tax": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": "Used when setting per channel is needed.",
            "label": "Override global tax settings.",
        },
        "include_taxes_in_prices": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": 'Applied only if "Override global tax settings" is on.',
            "label": "All products prices are entered with tax included.",
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
            override_global_tax=configuration["override_global_tax"],
            include_taxes_in_prices=configuration["include_taxes_in_prices"],
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
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value
        checkout_total = previous_value

        if not _validate_checkout(checkout_info, lines):
            return checkout_total
        response = get_checkout_tax_data(
            checkout_info, lines, self.config.tax_included, discounts, self.config
        )
        if not response or "error" in response:
            return checkout_total

        currency = checkout_info.checkout.currency
        taxed_total = zero_taxed_money(currency)

        for line in lines:
            taxed_line_total_data = self._calculate_checkout_line_total_price(
                taxes_data=response,
                item_code=line.variant.sku or line.variant.get_global_id(),
                tax_included=self.config.tax_included,
                # for some cases we will need a base_value but no need to call it for
                # each line
                base_value=SimpleLazyObject(  # type:ignore
                    lambda: base_calculations.calculate_base_line_total_price(
                        line, checkout_info.channel, discounts
                    )
                ),
            )
            taxed_total += taxed_line_total_data

        base_shipping_price = base_calculations.base_checkout_delivery_price(
            checkout_info, lines
        )
        shipping_price = self._calculate_checkout_shipping(
            currency, response.get("lines", []), base_shipping_price
        )

        taxed_total += shipping_price

        return max(
            taxed_total,
            zero_taxed_money(taxed_total.currency),
        )

    def _calculate_checkout_shipping(
        self, currency: str, lines: List[Dict], shipping_price: Money
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

        if currency == "JPY" and self.config.tax_included:
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
        discounts: Iterable[DiscountInfo],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        base_shipping_price = previous_value

        if not charge_taxes_on_shipping():
            return base_shipping_price

        if self._skip_plugin(previous_value):
            return base_shipping_price

        if not _validate_checkout(checkout_info, lines):
            return base_shipping_price

        response = get_checkout_tax_data(
            checkout_info, lines, self.config.tax_included, discounts, self.config
        )
        if not response or "error" in response:
            return base_shipping_price

        currency = str(response.get("currencyCode"))
        return self._calculate_checkout_shipping(
            currency, response.get("lines", []), base_shipping_price.net
        )

    def preprocess_order_creation(
        self,
        checkout_info: "CheckoutInfo",
        discounts: Iterable[DiscountInfo],
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

        data = generate_request_data_from_checkout(
            checkout_info,
            lines,
            self.config,
            self.config.tax_included,
            transaction_token=str(checkout_info.checkout.token),
            transaction_type=TransactionType.ORDER,
            discounts=discounts,
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
            customer_msg = CustomerErrors.get_error_msg(response.get("error", {}))
            raise TaxError(customer_msg)
        return previous_value

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active or order.is_unconfirmed():
            return previous_value
        request_data = get_order_request_data(
            order, self.config, self.config.tax_included
        )

        transaction_url = urljoin(
            get_api_url(self.config.use_sandbox), "transactions/createoradjust"
        )
        api_post_request_task.delay(
            transaction_url, request_data, asdict(self.config), order.id
        )
        return previous_value

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        return self.order_created(order, previous_value)

    def calculate_checkout_line_total(
        self,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        checkout_line_info: "CheckoutLineInfo",
        address: Optional["Address"],
        discounts: Iterable["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        base_total = previous_value
        if not checkout_line_info.product.charge_taxes:
            return base_total

        if not _validate_checkout(checkout_info, lines):
            return base_total

        taxes_data = get_checkout_tax_data(
            checkout_info, lines, self.config.tax_included, discounts, self.config
        )
        variant = checkout_line_info.variant

        return self._calculate_checkout_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            self.config.tax_included,
            previous_value,
        )

    @staticmethod
    def _calculate_checkout_line_total_price(
        taxes_data: Dict[str, Any],
        item_code: str,
        tax_included: bool,
        base_value: TaxedMoney,
    ) -> TaxedMoney:
        if not taxes_data or "error" in taxes_data:
            return base_value

        currency = taxes_data.get("currencyCode")

        for line in taxes_data.get("lines", []):
            if line.get("itemCode") != item_code:
                continue

            # The lineAmount does not include the discountAmount, but tax is calculated
            # for discounted net price, that take into account provided discount.
            tax = Decimal(line.get("tax", 0.0))
            discount_amount = Decimal(line.get("discountAmount", 0.0))
            net = Decimal(line["lineAmount"])

            if currency == "JPY" and tax_included:
                line_gross = base_value.gross
                line_net = Money(amount=line_gross.amount - tax, currency=currency)
            else:
                net -= discount_amount
                line_gross = Money(amount=net + tax, currency=currency)
                line_net = Money(amount=net, currency=currency)

            return TaxedMoney(net=line_net, gross=line_gross)
        return base_value

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
            return previous_value

        taxes_data = self._get_order_tax_data(order, previous_value)
        return self._calculate_order_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            self.config.tax_included,
            previous_value,
        )

    @staticmethod
    def _calculate_order_line_total_price(
        taxes_data: Dict[str, Any],
        item_code: str,
        tax_included: bool,
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

            if currency == "JPY" and tax_included:
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
        discounts: Iterable["DiscountInfo"],
        previous_value: TaxedMoney,
    ) -> TaxedMoney:
        if self._skip_plugin(previous_value):
            return previous_value

        base_total = previous_value
        if not checkout_line_info.product.charge_taxes:
            return base_total

        if not _validate_checkout(checkout_info, lines):
            return base_total

        variant = checkout_line_info.variant

        quantity = checkout_line_info.line.quantity
        taxes_data = get_checkout_tax_data(
            checkout_info, lines, self.config.tax_included, discounts, self.config
        )
        default_total = previous_value * quantity
        taxed_total_price = self._calculate_checkout_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            self.config.tax_included,
            default_total,
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
        if not variant or (variant and not product.charge_taxes):
            return previous_value

        quantity = order_line.quantity
        taxes_data = self._get_order_tax_data(order, previous_value)
        default_total = OrderTaxedPricesData(
            price_with_discounts=previous_value.price_with_discounts * quantity,
            undiscounted_price=previous_value.undiscounted_price * quantity,
        )
        taxed_total_prices_data = self._calculate_order_line_total_price(
            taxes_data,
            variant.sku or variant.get_global_id(),
            self.config.tax_included,
            default_total,
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

        if not charge_taxes_on_shipping():
            return previous_value

        if not _validate_order(order):
            return previous_value
        taxes_data = get_order_tax_data(
            order, self.config, self.config.tax_included, False
        )

        currency = taxes_data.get("currencyCode")
        for line in taxes_data.get("lines", []):
            if line["itemCode"] == "Shipping":
                tax = Decimal(line.get("tax", 0.0))
                net = Decimal(line.get("lineAmount", 0.0))
                if currency == "JPY" and self.config.tax_included:
                    gross = previous_value.gross
                    net = Money(amount=gross.amount - tax, currency=currency)
                else:
                    gross = Money(amount=net + tax, currency=currency)
                    net = Money(amount=net, currency=currency)
                return TaxedMoney(net=net, gross=gross)

        # Ignore typing checks because it is checked in _validate_order
        channel_listing = order.shipping_method.channel_listings.filter(  # type: ignore
            channel_id=order.channel_id
        ).first()
        if not channel_listing:
            return previous_value
        price = channel_listing.price
        return TaxedMoney(
            net=price,
            gross=price,
        )

    def get_tax_rate_type_choices(self, previous_value: Any) -> List[TaxType]:
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
        discounts: Iterable[DiscountInfo],
        previous_value: Decimal,
    ) -> Decimal:
        if not checkout_line_info.product.charge_taxes:
            return previous_value
        response = self._get_checkout_tax_data(
            checkout_info, lines, discounts, previous_value
        )
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
        if not product.charge_taxes:
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
        discounts: Iterable[DiscountInfo],
        previous_value: Decimal,
    ):
        response = self._get_checkout_tax_data(
            checkout_info, lines, discounts, previous_value
        )
        return self._get_shipping_tax_rate(response, previous_value)

    def get_order_shipping_tax_rate(self, order: "Order", previous_value: Decimal):
        response = self._get_order_tax_data(order, previous_value)
        return self._get_shipping_tax_rate(response, previous_value)

    def _get_checkout_tax_data(
        self,
        checkout_info: "CheckoutInfo",
        lines_info: Iterable["CheckoutLineInfo"],
        discounts: Iterable[DiscountInfo],
        base_value: Decimal,
    ):
        if self._skip_plugin(base_value):
            return None

        valid = _validate_checkout(checkout_info, lines_info)
        if not valid:
            return None

        response = get_checkout_tax_data(
            checkout_info, lines_info, self.config.tax_included, discounts, self.config
        )
        if not response or "error" in response:
            return None

        return response

    def _get_order_tax_data(
        self, order: "Order", base_value: Union[Decimal, OrderTaxedPricesData]
    ):
        if self._skip_plugin(base_value):
            return None

        valid = _validate_order(order)
        if not valid:
            return None

        response = get_order_tax_data(
            order, self.config, self.config.tax_included, False
        )
        if not response or "error" in response:
            return None

        return response

    @staticmethod
    def _get_unit_tax_rate(
        response: Dict[str, Any],
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
        response: Dict[str, Any],
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

    def assign_tax_code_to_object_meta(
        self,
        obj: Union["Product", "ProductType"],
        tax_code: Optional[str],
        previous_value: Any,
    ):
        if not self.active:
            return previous_value

        if tax_code is None and obj.pk:
            obj.delete_value_from_metadata(META_CODE_KEY)
            obj.delete_value_from_metadata(META_DESCRIPTION_KEY)
            return previous_value

        codes = get_cached_tax_codes_or_fetch(self.config)
        if tax_code not in codes:
            return previous_value

        tax_description = codes.get(tax_code)
        tax_item = {META_CODE_KEY: tax_code, META_DESCRIPTION_KEY: tax_description}
        obj.store_value_in_metadata(items=tax_item)
        return previous_value

    def get_tax_code_from_object_meta(
        self, obj: Union["Product", "ProductType"], previous_value: Any
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

    def show_taxes_on_storefront(self, previous_value: bool) -> bool:
        if not self.active:
            return previous_value
        return False

    def fetch_taxes_data(self, previous_value):
        if not self.active:
            return previous_value
        get_cached_tax_codes_or_fetch(self.config)
        return True

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
