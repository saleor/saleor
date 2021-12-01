import graphene

from ...core.permissions import CheckoutPermissions
from ..core.connection import create_connection_slice, filter_connection_queryset
from ..core.descriptions import ADDED_IN_31, DEPRECATED_IN_3X_FIELD
from ..core.fields import ConnectionField, FilterConnectionField
from ..core.scalars import UUID
from ..decorators import permission_required
from ..payment.mutations import CheckoutPaymentCreate
from .filters import CheckoutFilterInput
from .mutations import (
    CheckoutAddPromoCode,
    CheckoutBillingAddressUpdate,
    CheckoutComplete,
    CheckoutCreate,
    CheckoutCustomerAttach,
    CheckoutCustomerDetach,
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
)
from .resolvers import resolve_checkout, resolve_checkout_lines, resolve_checkouts
from .sorters import CheckoutSortingInput
from .types import (
    Checkout,
    CheckoutCountableConnection,
    CheckoutLineCountableConnection,
)


class CheckoutQueries(graphene.ObjectType):
    checkout = graphene.Field(
        Checkout,
        description="Look up a checkout by token and slug of channel.",
        token=graphene.Argument(UUID, description="The checkout's token."),
    )
    # FIXME we could optimize the below field
    checkouts = FilterConnectionField(
        CheckoutCountableConnection,
        sort_by=CheckoutSortingInput(description=f"{ADDED_IN_31} Sort checkouts."),
        filter=CheckoutFilterInput(
            description=f"{ADDED_IN_31} Filtering options for checkouts."
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of checkouts.",
    )
    checkout_lines = ConnectionField(
        CheckoutLineCountableConnection, description="List of checkout lines."
    )

    def resolve_checkout(self, info, token):
        return resolve_checkout(info, token)

    @permission_required(CheckoutPermissions.MANAGE_CHECKOUTS)
    def resolve_checkouts(self, info, *_args, channel=None, **kwargs):
        qs = resolve_checkouts(channel)
        qs = filter_connection_queryset(qs, kwargs)
        return create_connection_slice(qs, info, kwargs, CheckoutCountableConnection)

    @permission_required(CheckoutPermissions.MANAGE_CHECKOUTS)
    def resolve_checkout_lines(self, info, *_args, **kwargs):
        qs = resolve_checkout_lines()
        return create_connection_slice(
            qs, info, kwargs, CheckoutLineCountableConnection
        )


class CheckoutMutations(graphene.ObjectType):
    checkout_add_promo_code = CheckoutAddPromoCode.Field()
    checkout_billing_address_update = CheckoutBillingAddressUpdate.Field()
    checkout_complete = CheckoutComplete.Field()
    checkout_create = CheckoutCreate.Field()
    checkout_customer_attach = CheckoutCustomerAttach.Field()
    checkout_customer_detach = CheckoutCustomerDetach.Field()
    checkout_email_update = CheckoutEmailUpdate.Field()
    checkout_line_delete = CheckoutLineDelete.Field(
        deprecation_reason=(
            "DEPRECATED: Will be removed in Saleor 4.0. "
            "Use `checkoutLinesDelete` instead."
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
            f"{DEPRECATED_IN_3X_FIELD} " "Use `checkoutDeliveryMethodUpdate` instead."
        )
    )
    checkout_delivery_method_update = CheckoutDeliveryMethodUpdate.Field()
    checkout_language_code_update = CheckoutLanguageCodeUpdate.Field()
