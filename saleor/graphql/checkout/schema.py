import graphene

from ...core.permissions import CheckoutPermissions
from ..core.fields import BaseDjangoConnectionField, PrefetchingConnectionField
from ..decorators import permission_required
from ..payment.mutations import CheckoutPaymentCreate
from .mutations import (
    CheckoutAddPromoCode,
    CheckoutBillingAddressUpdate,
    CheckoutClearMeta,
    CheckoutClearPrivateMeta,
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
    CheckoutUpdateMeta,
    CheckoutUpdatePrivateMeta,
)
from .resolvers import resolve_checkout, resolve_checkout_lines, resolve_checkouts
from .types import Checkout, CheckoutLine


class CheckoutQueries(graphene.ObjectType):
    checkout = graphene.Field(
        Checkout,
        description="Look up a checkout by token.",
        token=graphene.Argument(graphene.UUID, description="The checkout's token."),
    )
    # FIXME we could optimize the below field
    checkouts = BaseDjangoConnectionField(Checkout, description="List of checkouts.")
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
    def resolve_checkouts(self, *_args, **_kwargs):
        resolve_checkouts()

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
    checkout_update_metadata = CheckoutUpdateMeta.Field(
        deprecation_reason=(
            "Use the `updateMetadata` mutation. This field will be removed after "
            "2020-07-31."
        )
    )
    checkout_clear_metadata = CheckoutClearMeta.Field(
        deprecation_reason=(
            "Use the `deleteMetadata` mutation. This field will be removed after "
            "2020-07-31."
        )
    )
    checkout_update_private_metadata = CheckoutUpdatePrivateMeta.Field(
        deprecation_reason=(
            "Use the `updatePrivateMetadata` mutation. This field will be removed "
            "after 2020-07-31."
        )
    )
    checkout_clear_private_metadata = CheckoutClearPrivateMeta.Field(
        deprecation_reason=(
            "Use the `deletePrivateMetadata` mutation. This field will be removed "
            "after 2020-07-31."
        )
    )
