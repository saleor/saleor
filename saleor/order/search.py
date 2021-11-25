from typing import TYPE_CHECKING

from ..account.search import (
    generate_address_search_document_value,
    generate_user_fields_search_document_value,
)

if TYPE_CHECKING:
    from .models import Order


def prepare_order_search_document_value(order: "Order"):
    search_document = str(order.id) + "\n"

    user_data = order.user_email + "\n"
    if user := order.user:
        user_data += generate_user_fields_search_document_value(user)
    search_document += user_data

    search_document += generate_order_payments_search_document_value(order)

    search_document += generate_order_discounts_search_document_value(order)

    search_document += generate_order_lines_search_document_value(order)

    for address_field in ["billing_address", "shipping_address"]:
        if address := getattr(order, address_field):
            search_document += generate_address_search_document_value(address)

    return search_document.lower()


def generate_order_payments_search_document_value(order: "Order"):
    payments_data = "\n".join(
        order.payments.exclude(psp_reference__isnull=True).values_list(  # type: ignore
            "psp_reference", flat=True
        )
    )
    if payments_data:
        payments_data += "\n"
    return payments_data


def generate_order_discounts_search_document_value(order: "Order"):
    discount_data = ""
    for data in order.discounts.values_list("name", "translated_name"):
        for value in data:
            if value:
                discount_data += value + "\n"
    return discount_data


def generate_order_lines_search_document_value(order: "Order"):
    lines_data = "\n".join(
        order.lines.exclude(product_sku__isnull=True).values_list(  # type: ignore
            "product_sku", flat=True
        )
    )
    if lines_data:
        lines_data += "\n"
    return lines_data
