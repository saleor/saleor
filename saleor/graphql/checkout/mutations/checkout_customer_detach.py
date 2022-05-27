import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ....core.exceptions import PermissionDenied
from ....core.permissions import AccountPermissions, AuthorizationFilters
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...utils import get_user_or_app_from_context
from ..types import Checkout
from .utils import get_checkout


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )

    class Meta:
        description = "Removes the user assigned as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        permissions = (
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_USER,
        )

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id=None, token=None, id=None):
        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=CheckoutErrorCode,
        )
        requestor = get_user_or_app_from_context(info.context)
        if not requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
            # Raise error if the current user doesn't own the checkout of the given ID.
            if checkout.user and checkout.user != info.context.user:
                raise PermissionDenied(
                    permissions=[AccountPermissions.IMPERSONATE_USER]
                )

        checkout.user = None
        checkout.save(update_fields=["user", "last_change"])

        info.context.plugins.checkout_updated(checkout)
        return CheckoutCustomerDetach(checkout=checkout)
