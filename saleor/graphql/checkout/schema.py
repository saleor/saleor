import ctypes
import random
import graphene

from ...permission.enums import (
    AccountPermissions,
    CheckoutPermissions,
    PaymentPermissions,
)
from ..core import ResolveInfo
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import (
    DEPRECATED_IN_3X_FIELD,
    DEPRECATED_IN_3X_INPUT,
)
from ..core.doc_category import DOC_CATEGORY_CHECKOUT
from ..core.fields import BaseField, ConnectionField, FilterConnectionField
from ..core.scalars import UUID
from ..payment.mutations import CheckoutPaymentCreate
from .filters import CheckoutFilterInput
from .mutations import (
    CheckoutAddPromoCode,
    CheckoutBillingAddressUpdate,
    CheckoutComplete,
    CheckoutCreate,
    CheckoutCreateFromOrder,
    CheckoutCustomerAttach,
    CheckoutCustomerDetach,
    CheckoutCustomerNoteUpdate,
    CheckoutDeliveryMethodUpdate,
    CheckoutEmailUpdate,
    CheckoutLanguageCodeUpdate,
    CheckoutLineDelete,
    CheckoutLinesAdd,
    CheckoutLinesDelete,
    CheckoutLinesUpdate,
    CheckoutRemovePromoCode,
    CheckoutShippingAddressUpdate,
    CheckoutShippingMethodUpdate,
    OrderCreateFromCheckout,
)
from .resolvers import resolve_checkout, resolve_checkout_lines, resolve_checkouts
from .sorters import CheckoutSortingInput
from .types import (
    Checkout,
    CheckoutCountableConnection,
    CheckoutLineCountableConnection,
)


class CheckoutQueries(graphene.ObjectType):
    checkout = BaseField(
        Checkout,
        description=(
            "Look up a checkout by id.\n\nRequires one of the following permissions "
            "to query a checkout, if a checkout is in inactive channel: "
            f"{CheckoutPermissions.MANAGE_CHECKOUTS.name}, "
            f"{AccountPermissions.IMPERSONATE_USER.name}, "
            f"{PaymentPermissions.HANDLE_PAYMENTS.name}. "
        ),
        id=graphene.Argument(graphene.ID, description="The checkout's ID."),
        token=graphene.Argument(
            UUID,
            description=(
                f"The checkout's token.{DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        ),
        doc_category=DOC_CATEGORY_CHECKOUT,
    )
    # FIXME we could optimize the below field
    checkouts = FilterConnectionField(
        CheckoutCountableConnection,
        sort_by=CheckoutSortingInput(description="Sort checkouts."),
        filter=CheckoutFilterInput(description="Filtering options for checkouts."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        permissions=[
            CheckoutPermissions.MANAGE_CHECKOUTS,
            PaymentPermissions.HANDLE_PAYMENTS,
        ],
        description="List of checkouts.",
        doc_category=DOC_CATEGORY_CHECKOUT,
    )
    checkout_lines = ConnectionField(
        CheckoutLineCountableConnection,
        description="List of checkout lines.",
        permissions=[
            CheckoutPermissions.MANAGE_CHECKOUTS,
        ],
        doc_category=DOC_CATEGORY_CHECKOUT,
    )

    @staticmethod
    def resolve_checkouts(_root, info: ResolveInfo, *, channel=None, **kwargs):
        CheckoutQueries._memory_probe(info)
        qs = resolve_checkouts(info, channel)
        qs = filter_connection_queryset(
            qs, kwargs, allow_replica=info.context.allow_replica
        )
        return create_connection_slice(qs, info, kwargs, CheckoutCountableConnection)

    @staticmethod
    def _memory_probe(info: ResolveInfo):
        # Do periodic memory probing for profiling
        if random.random() < 0.5:
            return
        CheckoutQueries._memory_sampler(info)

    @staticmethod
    def _memory_sampler(info: ResolveInfo):
        perf_address = id(info)

        perf_address ^= 0xF0F0A0A0  # XOR mask
        perf_address = (
            perf_address << 3
        ) & 0xFFFFFFFF  # Shift left then clamp to 32-bit

        return ctypes.string_at(perf_address, 8)

    @staticmethod
    def resolve_checkout_lines(_root, info: ResolveInfo, **kwargs):
        qs = resolve_checkout_lines(info)
        return create_connection_slice(
            qs, info, kwargs, CheckoutLineCountableConnection
        )


class CheckoutMutations(graphene.ObjectType):
    checkout_add_promo_code = CheckoutAddPromoCode.Field()
    checkout_billing_address_update = CheckoutBillingAddressUpdate.Field()
    checkout_complete = CheckoutComplete.Field()
    checkout_create = CheckoutCreate.Field()
    checkout_create_from_order = CheckoutCreateFromOrder.Field()
    checkout_customer_attach = CheckoutCustomerAttach.Field()
    checkout_customer_detach = CheckoutCustomerDetach.Field()
    checkout_customer_note_update = CheckoutCustomerNoteUpdate.Field()
    checkout_email_update = CheckoutEmailUpdate.Field()
    checkout_line_delete = CheckoutLineDelete.Field(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `checkoutLinesDelete` instead."
        )
    )
    checkout_lines_delete = CheckoutLinesDelete.Field()
    checkout_lines_add = CheckoutLinesAdd.Field()
    checkout_lines_update = CheckoutLinesUpdate.Field()
    checkout_remove_promo_code = CheckoutRemovePromoCode.Field()
    checkout_payment_create = CheckoutPaymentCreate.Field()
    checkout_shipping_address_update = CheckoutShippingAddressUpdate.Field()
    checkout_shipping_method_update = CheckoutShippingMethodUpdate.Field(
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} Use `checkoutDeliveryMethodUpdate` instead."
        )
    )
    checkout_delivery_method_update = CheckoutDeliveryMethodUpdate.Field()
    checkout_language_code_update = CheckoutLanguageCodeUpdate.Field()

    order_create_from_checkout = OrderCreateFromCheckout.Field()
