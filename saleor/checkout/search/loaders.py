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
