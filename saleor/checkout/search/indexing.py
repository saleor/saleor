from typing import TYPE_CHECKING

import graphene
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import transaction
from django.db.models import F, Q, Value

from ...account.search import generate_address_search_vector_value
from ...core.context import with_promise_context
from ...core.db.connection import allow_writer
from ...core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..lock_objects import checkout_qs_select_for_update
from ..models import Checkout
from .loaders import CheckoutData, CheckoutLineData, TransactionData, load_checkout_data

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ...payment.models import Payment
    from ..models import Checkout

MAX_INDEXED_LINES = 100
MAX_INDEXED_PAYMENTS = 100
MAX_INDEXED_TRANSACTIONS = 100


@allow_writer()
@with_promise_context
def update_checkouts_search_vector(checkouts: list["Checkout"]):
    """Update search vectors for multiple checkouts using efficient data loading."""
    checkout_data_map = load_checkout_data(checkouts)

    for checkout in checkouts:
        data = checkout_data_map.get(checkout.pk)
        if not data:
            continue

        checkout.search_vector = FlatConcatSearchVector(
            *prepare_checkout_search_vector_value(checkout, data)
        )
        checkout.search_index_dirty = False

    with transaction.atomic():
        _locked_checkouts = (
            checkout_qs_select_for_update()
            .filter(pk__in=[checkout.pk for checkout in checkouts])
            .values_list("pk", flat=True)
        )

        Checkout.objects.bulk_update(checkouts, ["search_vector", "search_index_dirty"])


def prepare_checkout_search_vector_value(
    checkout: "Checkout", data: CheckoutData
) -> list[NoValidationSearchVector]:
    """Prepare all search vector components for a checkout."""
    search_vectors = [
        NoValidationSearchVector(
            Value(str(checkout.token)), config="simple", weight="A"
        ),
    ]

    if checkout.email:
        search_vectors.append(
            NoValidationSearchVector(Value(checkout.email), config="simple", weight="A")
        )

    if data.user:
        search_vectors.append(
            NoValidationSearchVector(
                Value(data.user.email), config="simple", weight="A"
            )
        )
        search_vectors.append(
            NoValidationSearchVector(
                Value(data.user.first_name), config="simple", weight="A"
            )
        )
        search_vectors.append(
            NoValidationSearchVector(
                Value(data.user.last_name), config="simple", weight="A"
            )
        )

    if data.billing_address:
        search_vectors += generate_address_search_vector_value(
            data.billing_address, weight="B"
        )
    if data.shipping_address:
        search_vectors += generate_address_search_vector_value(
            data.shipping_address, weight="B"
        )

    search_vectors += generate_checkout_payments_search_vector_value(data.payments)
    search_vectors += generate_checkout_lines_search_vector_value(data.lines)
    search_vectors += generate_checkout_transactions_search_vector_value(
        data.transactions
    )
    return search_vectors


def generate_checkout_transactions_search_vector_value(
    transactions_data: list[TransactionData],
) -> list[NoValidationSearchVector]:
    """Generate search vectors for checkout transactions."""
    transaction_vectors = []
    for transaction_data in transactions_data[:MAX_INDEXED_TRANSACTIONS]:
        transaction = transaction_data.transaction
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

        for event in transaction_data.events:
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
    payments: list["Payment"],
) -> list[NoValidationSearchVector]:
    """Generate search vectors for checkout payments."""
    payment_vectors = []
    for payment in payments[:MAX_INDEXED_PAYMENTS]:
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
    lines_data: list[CheckoutLineData],
) -> list[NoValidationSearchVector]:
    """Generate search vectors for checkout lines."""
    line_vectors = []
    for line_data in lines_data[:MAX_INDEXED_LINES]:
        variant = line_data.variant
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

        product = line_data.product
        if product and product.name:
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

    return line_vectors


def search_checkouts(qs: "QuerySet[Checkout]", value) -> "QuerySet[Checkout]":
    """Filter checkouts by search query using the search_vector field."""
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
