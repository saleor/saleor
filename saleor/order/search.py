from functools import reduce
from operator import add
from typing import TYPE_CHECKING, Optional

import graphene
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import F, Q, Value, prefetch_related_objects

from ..account.search import generate_address_search_vector_value

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Order


def update_order_search_vector(order: "Order"):
    order.search_vector = prepare_order_search_vector_value(order)
    order.save(update_fields=["search_vector", "updated_at"])


def prepare_order_search_vector_value(order: "Order", *, already_prefetched=False):
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
    search_vector = SearchVector(Value(str(order.number)), config="simple", weight="A")
    if order.user_email:
        search_vector += SearchVector(
            Value(order.user_email), config="simple", weight="A"
        )
    if order.user:
        search_vector += SearchVector(
            Value(order.user.email), config="simple", weight="A"
        )
        if order.user.first_name:
            search_vector += SearchVector(
                Value(order.user.first_name), config="simple", weight="A"
            )
        if order.user.last_name:
            search_vector += SearchVector(
                Value(order.user.last_name), config="simple", weight="A"
            )

    if order.billing_address:
        search_vector += generate_address_search_vector_value(
            order.billing_address, weight="B"
        )
    if order.shipping_address:
        search_vector += generate_address_search_vector_value(
            order.shipping_address, weight="B"
        )

    payment_vector = generate_order_payments_search_vector_value(order)
    if payment_vector:
        search_vector += payment_vector
    discount_vector = generate_order_discounts_search_vector_value(order)
    if discount_vector:
        search_vector += discount_vector
    line_vector = generate_order_lines_search_vector_value(order)
    if line_vector:
        search_vector += line_vector

    return search_vector


def generate_order_payments_search_vector_value(
    order: "Order",
) -> Optional[SearchVector]:
    payment_vectors = []
    for payment in order.payments.all():
        payment_vectors.append(
            SearchVector(
                Value(graphene.Node.to_global_id("Payment", payment.id)),
                config="simple",
                weight="D",
            )
        )
        if payment.psp_reference:
            payment_vectors.append(
                SearchVector(
                    Value(payment.psp_reference),
                    config="simple",
                    weight="D",
                )
            )

    if not payment_vectors:
        return None

    search_vector = reduce(add, payment_vectors)

    return search_vector


def generate_order_discounts_search_vector_value(
    order: "Order",
) -> Optional[SearchVector]:
    discount_vectors = []
    for discount in order.discounts.all():
        if discount.name:
            discount_vectors.append(
                SearchVector(
                    Value(discount.name),
                    config="simple",
                    weight="D",
                )
            )
        if discount.translated_name:
            discount_vectors.append(
                SearchVector(
                    Value(discount.translated_name),
                    config="simple",
                    weight="D",
                )
            )

    if not discount_vectors:
        return None

    search_vector = reduce(add, discount_vectors)

    return search_vector


def generate_order_lines_search_vector_value(order: "Order") -> Optional[SearchVector]:
    line_vectors = []
    for line in order.lines.all():
        if line.product_sku:
            line_vectors.append(
                SearchVector(
                    Value(line.product_sku),
                    config="simple",
                    weight="C",
                )
            )
        if line.product_name:
            line_vectors.append(
                SearchVector(
                    Value(line.product_name),
                    config="simple",
                    weight="C",
                )
            )
        if line.variant_name:
            line_vectors.append(
                SearchVector(
                    Value(line.variant_name),
                    config="simple",
                    weight="C",
                )
            )
        if line.translated_product_name:
            line_vectors.append(
                SearchVector(
                    Value(line.translated_product_name),
                    config="simple",
                    weight="C",
                )
            )
        if line.translated_variant_name:
            line_vectors.append(
                SearchVector(
                    Value(line.translated_variant_name),
                    config="simple",
                    weight="C",
                )
            )

    if not line_vectors:
        return None

    search_vector = reduce(add, line_vectors)

    return search_vector


def search_orders(qs: "QuerySet[Order]", value) -> "QuerySet[Order]":
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
