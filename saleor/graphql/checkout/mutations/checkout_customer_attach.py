import graphene
from django.forms import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....core.exceptions import PermissionDenied
from ....core.permissions import AccountPermissions, AuthorizationFilters
from ...account.types import User
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils import get_user_or_app_from_context
from ..types import Checkout
from .utils import get_checkout


class CheckoutCustomerAttach(BaseMutation):
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
        customer_id = graphene.ID(
            required=False,
            description=(
                "ID of customer to attach to checkout. "
                "Requires IMPERSONATE_USER permission when customerId is different "
                "than the logged-in user."
            ),
        )

    class Meta:
        description = "Sets the customer as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        permissions = (
            AuthorizationFilters.AUTHENTICATED_APP,
            AuthorizationFilters.AUTHENTICATED_USER,
        )

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        /,
        checkout_id=None,
        token=None,
        customer_id=None,
        id=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        # Raise error when trying to attach a user to a checkout
        # that is already owned by another user.
        if checkout.user_id:
            raise PermissionDenied(
                message=(
                    "You cannot reassign a checkout that is already attached to a "
                    "user."
                )
            )

        user_id_from_request = None
        if user := info.context.user:
            user_id_from_request = graphene.Node.to_global_id("User", user.id)

        if customer_id and customer_id != user_id_from_request:
            requestor = get_user_or_app_from_context(info.context)
            if not requestor or not requestor.has_perm(
                AccountPermissions.IMPERSONATE_USER
            ):
                raise PermissionDenied(
                    permissions=[AccountPermissions.IMPERSONATE_USER]
                )
            customer = cls.get_node_or_error(info, customer_id, only_type=User)
        elif not info.context.user:
            raise ValidationError(
                {
                    "customer_id": ValidationError(
                        "The customerId value must be provided "
                        "when running mutation as app.",
                        code=CheckoutErrorCode.REQUIRED.value,
                    )
                }
            )
        else:
            customer = info.context.user

        checkout.user = customer
        checkout.email = customer.email
        checkout.save(update_fields=["email", "user", "last_change"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.checkout_updated, checkout)
        return CheckoutCustomerAttach(checkout=checkout)
