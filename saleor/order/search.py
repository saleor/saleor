from typing import TYPE_CHECKING

import graphene
from django.db.models import Q

from ..account.search import (
    generate_address_search_document_value,
    generate_user_fields_search_document_value,
)

if TYPE_CHECKING:
    from .models import Order


def update_order_search_document(order: "Order"):
    order.search_document = prepare_order_search_document_value(order)
    order.save(update_fields=["search_document"])


def prepare_order_search_document_value(order: "Order"):
    search_document = str(order.id) + "\n"

    user_data = order.user_email + "\n"
    if user := order.user:
        user_data += generate_user_fields_search_document_value(user)
    search_document += user_data

    for address_field in ["billing_address", "shipping_address"]:
        if address := getattr(order, address_field):
            search_document += generate_address_search_document_value(address)

    search_document += generate_order_payments_search_document_value(order)

    search_document += generate_order_discounts_search_document_value(order)

    search_document += generate_order_lines_search_document_value(order)

    return search_document.lower()


def generate_order_payments_search_document_value(order: "Order"):
    payments_data = ""
    for id, psp_reference in order.payments.values_list("id", "psp_reference"):
        payments_data += graphene.Node.to_global_id("Payment", id) + "\n"
        if psp_reference:
            payments_data += psp_reference + "\n"
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


def search_orders(qs, value):
    if value:
        lookup = Q()
        for val in value.split():
            if val.startswith("#"):
                val = val[1:]
            lookup &= Q(search_document__ilike=val)
        qs = qs.filter(lookup)
    return qs
