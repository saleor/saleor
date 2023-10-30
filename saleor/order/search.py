from typing import TYPE_CHECKING

import graphene
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, Value, prefetch_related_objects

from ..account.search import generate_address_search_vector_value
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Order


def update_order_search_vector(order: "Order", *, save: bool = True):
    order.search_vector = FlatConcatSearchVector(
        *prepare_order_search_vector_value(order)
    )
    if save:
        order.save(update_fields=["search_vector", "updated_at"])


def prepare_order_search_vector_value(
    order: "Order", *, already_prefetched=False
) -> list[NoValidationSearchVector]:
    if not already_prefetched:
        prefetch_related_objects(
            [order],
            "user",
            "billing_address",
            "shipping_address",
            "payments",
            "discounts",
            "lines",
            "payment_transactions__events",
        )
    search_vectors = [
        NoValidationSearchVector(Value(str(order.number)), config="simple", weight="A")
    ]
    if order.user_email:
        search_vectors.append(
            NoValidationSearchVector(
                Value(order.user_email), config="simple", weight="A"
            )
        )
    if order.user:
        search_vectors.append(
            NoValidationSearchVector(
                Value(order.user.email), config="simple", weight="A"
            )
        )
        if order.user.first_name:
            search_vectors.append(
                NoValidationSearchVector(
                    Value(order.user.first_name), config="simple", weight="A"
                )
            )
        if order.user.last_name:
            search_vectors.append(
                NoValidationSearchVector(
                    Value(order.user.last_name), config="simple", weight="A"
                )
            )

    if order.billing_address:
        search_vectors += generate_address_search_vector_value(
            order.billing_address, weight="B"
        )
    if order.shipping_address:
        search_vectors += generate_address_search_vector_value(
            order.shipping_address, weight="B"
        )

    search_vectors += generate_order_payments_search_vector_value(order)
    search_vectors += generate_order_discounts_search_vector_value(order)
    search_vectors += generate_order_lines_search_vector_value(order)
    search_vectors += generate_order_transactions_search_vector_value(order)
    return search_vectors


def generate_order_transactions_search_vector_value(
    order: "Order",
) -> list[NoValidationSearchVector]:
    transaction_vectors = []
    for transaction in order.payment_transactions.all()[
        : settings.SEARCH_ORDERS_MAX_INDEXED_TRANSACTIONS
    ]:
        transaction_vectors.append(
            NoValidationSearchVector(
                Value(graphene.Node.to_global_id("TransactionItem", transaction.token)),
                config="simple",
                weight="D",
            )
        )
        if transaction.psp_reference:
            transaction_vectors.append(
                NoValidationSearchVector(
                    Value(transaction.psp_reference),
                    config="simple",
                    weight="D",
                )
            )
        for event in transaction.events.all()[
            : settings.SEARCH_ORDERS_MAX_INDEXED_TRANSACTIONS
        ]:
            if event.psp_reference:
                transaction_vectors.append(
                    NoValidationSearchVector(
                        Value(event.psp_reference),
                        config="simple",
                        weight="D",
                    )
                )
    return transaction_vectors


def generate_order_payments_search_vector_value(
    order: "Order",
) -> list[NoValidationSearchVector]:
    payment_vectors = []
    for payment in order.payments.all()[: settings.SEARCH_ORDERS_MAX_INDEXED_PAYMENTS]:
        payment_vectors.append(
            NoValidationSearchVector(
                Value(graphene.Node.to_global_id("Payment", payment.id)),
                config="simple",
                weight="D",
            )
        )
        if payment.psp_reference:
            payment_vectors.append(
                NoValidationSearchVector(
                    Value(payment.psp_reference),
                    config="simple",
                    weight="D",
                )
            )
    return payment_vectors


def generate_order_discounts_search_vector_value(
    order: "Order",
) -> list[NoValidationSearchVector]:
    discount_vectors = []
    for discount in order.discounts.all()[
        : settings.SEARCH_ORDERS_MAX_INDEXED_DISCOUNTS
    ]:
        if discount.name:
            discount_vectors.append(
                NoValidationSearchVector(
                    Value(discount.name),
                    config="simple",
                    weight="D",
                )
            )
        if discount.translated_name:
            discount_vectors.append(
                NoValidationSearchVector(
                    Value(discount.translated_name),
                    config="simple",
                    weight="D",
                )
            )
    return discount_vectors


def generate_order_lines_search_vector_value(
    order: "Order",
) -> list[NoValidationSearchVector]:
    line_vectors = []
    for line in order.lines.all()[: settings.SEARCH_ORDERS_MAX_INDEXED_LINES]:
        if line.product_sku:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(line.product_sku),
                    config="simple",
                    weight="C",
                )
            )
        if line.product_name:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(line.product_name),
                    config="simple",
                    weight="C",
                )
            )
        if line.variant_name:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(line.variant_name),
                    config="simple",
                    weight="C",
                )
            )
        if line.translated_product_name:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(line.translated_product_name),
                    config="simple",
                    weight="C",
                )
            )
        if line.translated_variant_name:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(line.translated_variant_name),
                    config="simple",
                    weight="C",
                )
            )
    return line_vectors


def search_orders(qs: "QuerySet[Order]", value) -> "QuerySet[Order]":
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
