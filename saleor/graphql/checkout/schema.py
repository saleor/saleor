import graphene

from ...core.permissions import CheckoutPermissions
from ..core.fields import BaseDjangoConnectionField, PrefetchingConnectionField
from ..core.scalars import UUID
from ..decorators import permission_required
from ..payment.mutations import CheckoutPaymentCreate
from .mutations import (
    CheckoutAddPromoCode,
    CheckoutBillingAddressUpdate,
    CheckoutComplete,
    CheckoutCreate,
    CheckoutCustomerAttach,
    CheckoutCustomerDetach,
    CheckoutEmailUpdate,
    CheckoutLineDelete,
    CheckoutLinesAdd,
    CheckoutLinesUpdate,
    CheckoutRemovePromoCode,
    CheckoutShippingAddressUpdate,
    CheckoutShippingMethodUpdate,
)
from .resolvers import resolve_checkout, resolve_checkout_lines, resolve_checkouts
from .types import Checkout, CheckoutLine


class CheckoutQueries(graphene.ObjectType):
    checkout = graphene.Field(
        Checkout,
        description="Look up a checkout by token and slug of channel.",
        token=graphene.Argument(UUID, description="The checkout's token."),
    )
    # FIXME we could optimize the below field
    checkouts = BaseDjangoConnectionField(
        Checkout,
        description="List of checkouts.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    checkout_line = graphene.Field(
        CheckoutLine,
        id=graphene.Argument(graphene.ID, description="ID of the checkout line."),
        description="Look up a checkout line by ID.",
    )
    checkout_lines = PrefetchingConnectionField(
        CheckoutLine, description="List of checkout lines."
    )

    def resolve_checkout(self, info, token):
        return resolve_checkout(info, token)

    @permission_required(CheckoutPermissions.MANAGE_CHECKOUTS)
    def resolve_checkouts(self, *_args, channel=None, **_kwargs):
        return resolve_checkouts(channel)

    def resolve_checkout_line(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, CheckoutLine)

    @permission_required(CheckoutPermissions.MANAGE_CHECKOUTS)
    def resolve_checkout_lines(self, *_args, **_kwargs):
        return resolve_checkout_lines()


class CheckoutMutations(graphene.ObjectType):
    checkout_add_promo_code = CheckoutAddPromoCode.Field()
    checkout_billing_address_update = CheckoutBillingAddressUpdate.Field()
    checkout_complete = CheckoutComplete.Field()
    checkout_create = CheckoutCreate.Field()
    checkout_customer_attach = CheckoutCustomerAttach.Field()
    checkout_customer_detach = CheckoutCustomerDetach.Field()
    checkout_email_update = CheckoutEmailUpdate.Field()
    checkout_line_delete = CheckoutLineDelete.Field()
    checkout_lines_add = CheckoutLinesAdd.Field()
    checkout_lines_update = CheckoutLinesUpdate.Field()
    checkout_remove_promo_code = CheckoutRemovePromoCode.Field()
    checkout_payment_create = CheckoutPaymentCreate.Field()
    checkout_shipping_address_update = CheckoutShippingAddressUpdate.Field()
    checkout_shipping_method_update = CheckoutShippingMethodUpdate.Field()
