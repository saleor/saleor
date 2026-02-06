from itertools import chain
from typing import TYPE_CHECKING, NamedTuple
from uuid import UUID

from ...graphql.account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ...graphql.checkout.dataloaders.models import (
    CheckoutLinesByCheckoutTokenLoader,
    TransactionItemsByCheckoutIDLoader,
)
from ...graphql.core.context import SaleorContext
from ...graphql.payment.dataloaders import (
    PaymentsByCheckoutTokenLoader,
    TransactionEventByTransactionIdLoader,
)
from ...graphql.product.dataloaders.products import (
    ProductByIdLoader,
    ProductVariantByIdLoader,
)

if TYPE_CHECKING:
    from ...account.models import Address, User
    from ...payment.models import Payment, TransactionEvent, TransactionItem
    from ...product.models import Product, ProductVariant
    from ..models import Checkout, CheckoutLine


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


def load_checkout_data(checkouts: list["Checkout"]) -> dict[UUID, CheckoutData]:
    """Load all related data for checkouts using dataloaders for efficient querying."""
    context = SaleorContext()
    checkout_ids = [checkout.pk for checkout in checkouts]

    user_map = _load_users(context, checkouts)
    address_map = _load_addresses(context, checkouts)

    payments_list = PaymentsByCheckoutTokenLoader(context).load_many(checkout_ids).get()
    lines_list = (
        CheckoutLinesByCheckoutTokenLoader(context).load_many(checkout_ids).get()
    )
    transactions_list = (
        TransactionItemsByCheckoutIDLoader(context).load_many(checkout_ids).get()
    )

    all_lines = list(chain.from_iterable(lines_list))
    variant_map, product_map = _load_variants_and_products(context, all_lines)

    all_transactions = list(chain.from_iterable(transactions_list))
    transaction_events_map = _load_transaction_events(context, all_transactions)

    payments_by_checkout = dict(zip(checkout_ids, payments_list, strict=False))
    lines_by_checkout = dict(zip(checkout_ids, lines_list, strict=False))
    transactions_by_checkout = dict(zip(checkout_ids, transactions_list, strict=False))

    result = {}
    for checkout in checkouts:
        c_lines = lines_by_checkout.get(checkout.pk, [])
        line_data_list = _build_checkout_line_data(c_lines, variant_map, product_map)

        c_transactions = transactions_by_checkout.get(checkout.pk, [])
        transaction_data_list = _build_transaction_data(
            c_transactions, transaction_events_map
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


def _load_users(
    context: SaleorContext, checkouts: list["Checkout"]
) -> dict[int, "User"]:
    """Load users for checkouts."""
    users = (
        UserByUserIdLoader(context)
        .load_many([c.user_id for c in checkouts if c.user_id])
        .get()
    )
    return {user.id: user for user in users if user}


def _load_addresses(
    context: SaleorContext, checkouts: list["Checkout"]
) -> dict[int, "Address"]:
    """Load billing and shipping addresses for checkouts."""
    address_ids = {c.billing_address_id for c in checkouts if c.billing_address_id}
    address_ids.update(
        {c.shipping_address_id for c in checkouts if c.shipping_address_id}
    )
    addresses = AddressByIdLoader(context).load_many(list(address_ids)).get()
    return {addr.id: addr for addr in addresses if addr}


def _load_variants_and_products(
    context: SaleorContext, lines: list["CheckoutLine"]
) -> tuple[dict[int, "ProductVariant"], dict[int, "Product"]]:
    """Load variants and products for checkout lines."""
    variant_ids = [line.variant_id for line in lines if line.variant_id]
    variants = ProductVariantByIdLoader(context).load_many(variant_ids).get()
    variant_map = {v.id: v for v in variants if v}

    product_ids = [v.product_id for v in variants if v]
    products = ProductByIdLoader(context).load_many(product_ids).get()
    product_map = {p.id: p for p in products if p}

    return variant_map, product_map


def _load_transaction_events(
    context: SaleorContext, transactions: list["TransactionItem"]
) -> dict[int, list["TransactionEvent"]]:
    """Load transaction events for transactions."""
    transaction_ids = [t.id for t in transactions]
    transaction_events_list = (
        TransactionEventByTransactionIdLoader(context).load_many(transaction_ids).get()
    )
    return dict(zip(transaction_ids, transaction_events_list, strict=False))


def _build_checkout_line_data(
    lines: list["CheckoutLine"],
    variant_map: dict[int, "ProductVariant"],
    product_map: dict[int, "Product"],
) -> list[CheckoutLineData]:
    """Build CheckoutLineData objects from lines and related data."""
    line_data_list = []
    for line in lines:
        variant = variant_map.get(line.variant_id)
        product = product_map.get(variant.product_id) if variant else None
        line_data_list.append(
            CheckoutLineData(line=line, variant=variant, product=product)
        )
    return line_data_list


def _build_transaction_data(
    transactions: list["TransactionItem"],
    transaction_events_map: dict[int, list["TransactionEvent"]],
) -> list[TransactionData]:
    """Build TransactionData objects from transactions and events."""
    transaction_data_list = []
    for transaction_item in transactions:
        events = transaction_events_map.get(transaction_item.id, [])
        transaction_data_list.append(
            TransactionData(transaction=transaction_item, events=events)
        )
    return transaction_data_list
