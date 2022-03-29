from typing import TYPE_CHECKING

import graphene
from django.db.models import Q, prefetch_related_objects

from ..account.search import (
    generate_address_search_document_value,
    generate_user_fields_search_document_value,
)

if TYPE_CHECKING:
    from .models import Order


def update_order_search_document(order: "Order"):
    order.search_document = prepare_order_search_document_value(order)
    order.save(update_fields=["search_document", "updated_at"])


def prepare_order_search_document_value(order: "Order", *, already_prefetched=False):
    if not already_prefetched:
        prefetch_related_objects(
            [order],
            "user",
            "billing_address",
            "shipping_address",
            "payments",
            "discounts",
            "lines",
        )
    search_document = f"#{str(order.number)}\n"
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
    for payment in order.payments.all():
        payments_data += graphene.Node.to_global_id("Payment", payment.id) + "\n"
        if psp_reference := payment.psp_reference:
            payments_data += psp_reference + "\n"
    return payments_data


def generate_order_discounts_search_document_value(order: "Order"):
    discount_data = ""
    for discount in order.discounts.all():
        for field in ["name", "translated_name"]:
            if value := getattr(discount, field):
                discount_data += value + "\n"
    return discount_data


def generate_order_lines_search_document_value(order: "Order"):
    lines_data = "\n".join(
        [line.product_sku for line in order.lines.all() if line.product_sku]
    )
    if lines_data:
        lines_data += "\n"
    return lines_data


def search_orders(qs, value):
    if value:
        lookup = Q()
        for val in value.split():
            lookup &= Q(search_document__ilike=val)
        qs = qs.filter(lookup)
    return qs
