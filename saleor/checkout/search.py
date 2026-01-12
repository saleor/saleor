from typing import TYPE_CHECKING, NamedTuple
from uuid import UUID

import graphene
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import transaction
from django.db.models import F, Q, Value

from ..account.search import generate_address_search_vector_value
from ..core.context import with_promise_context
from ..core.db.connection import allow_writer
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from ..graphql.account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..graphql.checkout.dataloaders.models import (
    CheckoutLinesByCheckoutTokenLoader,
    TransactionItemsByCheckoutIDLoader,
)
from ..graphql.core.context import SaleorContext
from ..graphql.payment.dataloaders import (
    PaymentsByCheckoutTokenLoader,
    TransactionEventByTransactionIdLoader,
)
from ..graphql.product.dataloaders.products import (
    ProductByIdLoader,
    ProductVariantByIdLoader,
)
from ..payment.models import Payment
from .models import Checkout

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from ..account.models import Address, User
    from ..checkout.models import CheckoutLine
    from ..payment.models import Payment, TransactionEvent, TransactionItem
    from ..product.models import Product, ProductVariant

MAX_INDEXED_LINES = 100
MAX_INDEXED_PAYMENTS = 100
MAX_INDEXED_TRANSACTIONS = 100


class CheckoutLineData(NamedTuple):
    line: "CheckoutLine"
    variant: "ProductVariant | None"
    product: "Product | None"


class TransactionData(NamedTuple):
    transaction: "TransactionItem"
    events: list["TransactionEvent"]


class CheckoutData(NamedTuple):
    user: "User | None"
    billing_address: "Address | None"
    shipping_address: "Address | None"
    payments: list["Payment"]
    lines: list[CheckoutLineData]
    transactions: list[TransactionData]


@allow_writer()
@with_promise_context
def update_checkouts_search_vector(checkouts: list[Checkout]):
    checkout_data_map = _load_checkout_data(checkouts)

    for checkout in checkouts:
        data = checkout_data_map.get(checkout.pk)
        if not data:
            continue

        checkout.search_vector = FlatConcatSearchVector(
            *prepare_checkout_search_vector_value(checkout, data)
        )

    with transaction.atomic():
        Checkout.objects.bulk_update(checkouts, ["search_vector", "last_change"])


def _load_checkout_data(checkouts: list[Checkout]) -> dict[UUID, CheckoutData]:
    context = SaleorContext()
    checkout_ids = [checkout.pk for checkout in checkouts]

    # Level 1: Direct relations and Lists
    users = (
        UserByUserIdLoader(context)
        .load_many([c.user_id for c in checkouts if c.user_id])
        .get()
    )
    user_map = {user.id: user for user in users if user}

    address_ids = {c.billing_address_id for c in checkouts if c.billing_address_id}
    address_ids.update(
        {c.shipping_address_id for c in checkouts if c.shipping_address_id}
    )
    addresses = AddressByIdLoader(context).load_many(list(address_ids)).get()
    address_map = {addr.id: addr for addr in addresses if addr}

    payments_list = PaymentsByCheckoutTokenLoader(context).load_many(checkout_ids).get()
    lines_list = (
        CheckoutLinesByCheckoutTokenLoader(context).load_many(checkout_ids).get()
    )
    transactions_list = (
        TransactionItemsByCheckoutIDLoader(context).load_many(checkout_ids).get()
    )

    # Prepare for Level 2 (Nested in Lines and Transactions)
    all_lines = [line for lines in lines_list for line in lines]
    variant_ids = [line.variant_id for line in all_lines if line.variant_id]

    variants = ProductVariantByIdLoader(context).load_many(variant_ids).get()
    variant_map = {v.id: v for v in variants if v}

    product_ids = [v.product_id for v in variants if v]
    products = ProductByIdLoader(context).load_many(product_ids).get()
    product_map = {p.id: p for p in products if p}

    # Transaction Events
    all_transactions = [t for txs in transactions_list for t in txs]
    transaction_ids = [t.id for t in all_transactions]
    transaction_events_list = (
        TransactionEventByTransactionIdLoader(context).load_many(transaction_ids).get()
    )
    transaction_events_map = dict(
        zip(transaction_ids, transaction_events_list, strict=False)
    )

    # Assemble Result
    result = {}

    # Pre-map lists to checkout_id
    payments_by_checkout = dict(zip(checkout_ids, payments_list, strict=False))
    lines_by_checkout = dict(zip(checkout_ids, lines_list, strict=False))
    transactions_by_checkout = dict(zip(checkout_ids, transactions_list, strict=False))

    for checkout in checkouts:
        c_lines = lines_by_checkout.get(checkout.pk, [])
        line_data_list = []
        for line in c_lines:
            variant = variant_map.get(line.variant_id)
            product = product_map.get(variant.product_id) if variant else None

            line_data_list.append(
                CheckoutLineData(
                    line=line,
                    variant=variant,
                    product=product,
                )
            )

        c_transactions = transactions_by_checkout.get(checkout.pk, [])
        transaction_data_list = []
        for transaction_item in c_transactions:
            events = transaction_events_map.get(transaction_item.id, [])
            transaction_data_list.append(
                TransactionData(transaction=transaction_item, events=events)
            )

        result[checkout.pk] = CheckoutData(
            user=user_map.get(checkout.user_id) if checkout.user_id else None,
            billing_address=address_map.get(checkout.billing_address_id)
            if checkout.billing_address_id
            else None,
            shipping_address=address_map.get(checkout.shipping_address_id)
            if checkout.shipping_address_id
            else None,
            payments=payments_by_checkout.get(checkout.pk, []),
            lines=line_data_list,
            transactions=transaction_data_list,
        )

    return result


def prepare_checkout_search_vector_value(
    checkout: "Checkout", data: CheckoutData
) -> list[NoValidationSearchVector]:
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
    payment_vectors = []
    for payment in payments[:MAX_INDEXED_PAYMENTS]:
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
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
