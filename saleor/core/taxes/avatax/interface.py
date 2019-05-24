from collections import defaultdict
from datetime import date
from decimal import Decimal
from urllib.parse import urljoin

from prices import Money, TaxedMoney

from ....checkout.models import Checkout
from ....discount.models import Sale
from ....order.models import Order
from ..errors import TaxError
from . import (
    TransactionType,
    api_post_request,
    generate_request_data,
    get_api_url,
    get_checkout_tax_data,
    validate_checkout,
)


def get_total_gross(checkout: "Checkout", discounts):
    if not validate_checkout(checkout):
        return checkout.get_total(discounts=discounts)
    response = get_checkout_tax_data(checkout, discounts)
    tax = Decimal(response.get("totalTax", "0.0"))
    total_net = checkout.get_total(discounts=discounts).net
    total_gross = Money(amount=total_net.amount + tax, currency=total_net.currency)
    total = TaxedMoney(net=total_net, gross=total_gross)

    return total


def get_subtotal_gross(checkout: "Checkout", discounts):
    if not validate_checkout(checkout):
        return checkout.get_subtotal(discounts)
    response = get_checkout_tax_data(checkout, discounts)

    sub_tax = Decimal(0.0)
    for line in response.get("lines", []):
        if line["itemCode"] == "Shipping":
            continue
        sub_tax += Decimal(line["tax"])
    sub_total_net = checkout.get_subtotal(discounts).net
    sub_total_gross = Money(sub_total_net.amount + sub_tax, sub_total_net.currency)
    sub_total = TaxedMoney(net=sub_total_net, gross=sub_total_gross)
    return sub_total


def get_shipping_gross(checkout: "Checkout", discounts):
    if not validate_checkout(checkout):
        return checkout.get_shipping_price(None)
    response = get_checkout_tax_data(checkout, discounts)

    shipping_tax = Decimal(0.0)
    for line in response.get("lines", []):
        if line["itemCode"] == "Shipping":
            shipping_tax = Decimal(line["tax"])
            break

    shipping_net = checkout.get_shipping_price(None).net
    shipping_gross = Money(shipping_net.amount + shipping_tax, shipping_net.currency)
    shipping_total = TaxedMoney(net=shipping_net, gross=shipping_gross)

    return shipping_total


def get_lines_with_taxes(checkout: "Checkout", discounts):
    """Calculate and return tuple (line, unit_tax)"""
    lines_taxes = defaultdict(lambda: Decimal("0.0"))

    if validate_checkout(checkout):
        response = get_checkout_tax_data(checkout, discounts)

        for line in response.get("lines", []):
            if line["itemCode"] == "Shipping":
                continue
            tax = line.get("tax")
            quantity = line.get("quantity")
            if tax and quantity:
                tax = Decimal(tax / int(quantity))
                lines_taxes[line["itemCode"]] = tax

    return [(line, lines_taxes[line.variant.sku]) for line in checkout.lines.all()]


def postprocess_order_creation_with_taxes(order: "Order"):
    # FIXME this can be a celery task (?)
    # FIXME maybe we can figure out better name

    checkout = Checkout.objects.get(token=order.checkout_token)
    discounts = Sale.objects.active(date.today()).prefetch_related(
        "products", "categories", "collections"
    )
    data = generate_request_data(
        checkout,
        transaction_token=str(order.token),
        transaction_type=TransactionType.INVOICE,
        discounts=discounts,
    )
    transaction_url = urljoin(get_api_url(), "transactions/create")
    response = api_post_request(transaction_url, data)
    # FIXME errors for users (?)
    if not response or "error" in response:
        raise TaxError(response.get("error", {}).get("message", ""))
