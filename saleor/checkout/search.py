from typing import TYPE_CHECKING

import graphene
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, Value, prefetch_related_objects

from ..account.search import generate_address_search_vector_value
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import Checkout

MAX_INDEXED_LINES = 100
MAX_INDEXED_PAYMENTS = 100
MAX_INDEXED_TRANSACTIONS = 100


def update_checkout_search_vector(checkout: "Checkout", *, save: bool = True):
    checkout.search_vector = FlatConcatSearchVector(
        *prepare_checkout_search_vector_value(checkout)
    )
    if save:
        checkout.save(update_fields=["search_vector", "last_change"])


def prepare_checkout_search_vector_value(
    checkout: "Checkout", *, already_prefetched=False
) -> list[NoValidationSearchVector]:
    if not already_prefetched:
        prefetch_related_objects(
            [checkout],
            "user",
            "billing_address__country",
            "shipping_address__country",
            "payments",
            "lines__variant__product__translations",
            "lines__variant__translations",
            "payment_transactions__events",
        )
    search_vectors = [
        NoValidationSearchVector(
            Value(str(checkout.token)), config="simple", weight="A"
        ),
    ]

    if checkout.email:
        search_vectors.append(
            NoValidationSearchVector(Value(checkout.email), config="simple", weight="A")
        )

    if checkout.user:
        search_vectors.append(
            NoValidationSearchVector(
                Value(checkout.user.email), config="simple", weight="A"
            )
        )
        if checkout.user.first_name:
            search_vectors.append(
                NoValidationSearchVector(
                    Value(checkout.user.first_name), config="simple", weight="A"
                )
            )
        if checkout.user.last_name:
            search_vectors.append(
                NoValidationSearchVector(
                    Value(checkout.user.last_name), config="simple", weight="A"
                )
            )

    if checkout.billing_address:
        search_vectors += generate_address_search_vector_value(
            checkout.billing_address, weight="B"
        )
    if checkout.shipping_address:
        search_vectors += generate_address_search_vector_value(
            checkout.shipping_address, weight="B"
        )

    search_vectors += generate_checkout_payments_search_vector_value(checkout)
    search_vectors += generate_checkout_lines_search_vector_value(checkout)
    search_vectors += generate_checkout_transactions_search_vector_value(checkout)
    return search_vectors


def generate_checkout_transactions_search_vector_value(
    checkout: "Checkout",
) -> list[NoValidationSearchVector]:
    transaction_vectors = []
    for transaction in checkout.payment_transactions.all()[:MAX_INDEXED_TRANSACTIONS]:
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
        for event in transaction.events.all()[:MAX_INDEXED_TRANSACTIONS]:
            if event.psp_reference:
                transaction_vectors.append(
                    NoValidationSearchVector(
                        Value(event.psp_reference),
                        config="simple",
                        weight="D",
                    )
                )
    return transaction_vectors


def generate_checkout_payments_search_vector_value(
    checkout: "Checkout",
) -> list[NoValidationSearchVector]:
    payment_vectors = []
    for payment in checkout.payments.all()[:MAX_INDEXED_PAYMENTS]:
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


def generate_checkout_lines_search_vector_value(
    checkout: "Checkout",
) -> list[NoValidationSearchVector]:
    line_vectors = []
    for line in checkout.lines.all()[:MAX_INDEXED_LINES]:
        variant = line.variant
        if not variant:
            continue

        if variant.sku:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(variant.sku),
                    config="simple",
                    weight="C",
                )
            )

        product = variant.product
        if product.name:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(product.name),
                    config="simple",
                    weight="C",
                )
            )
        if variant.name:
            line_vectors.append(
                NoValidationSearchVector(
                    Value(variant.name),
                    config="simple",
                    weight="C",
                )
            )

        # Translated product names
        for translation in product.translations.all():
            if translation.name:
                line_vectors.append(
                    NoValidationSearchVector(
                        Value(translation.name),
                        config="simple",
                        weight="C",
                    )
                )

        # Translated variant names
        for translation in variant.translations.all():
            if translation.name:
                line_vectors.append(
                    NoValidationSearchVector(
                        Value(translation.name),
                        config="simple",
                        weight="C",
                    )
                )

    return line_vectors


def search_checkouts(qs: "QuerySet[Checkout]", value) -> "QuerySet[Checkout]":
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
