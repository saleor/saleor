import graphene
from django.forms import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....core.exceptions import PermissionDenied
from ....core.permissions import AccountPermissions, AuthorizationFilters
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.validators import validate_one_of_args_is_in_mutation
from ...utils import get_user_or_app_from_context
from ..types import Checkout
from .utils import get_checkout_by_token


class CheckoutCustomerAttach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
        )
        customer_id = graphene.ID(
            required=False,
            description=(
                "ID of customer to attach to checkout. Can be used to attach customer "
                "to checkout by staff or app. Requires IMPERSONATE_USER permission."
            ),
        )
        token = UUID(description="Checkout token.", required=False)

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
        cls, _root, info, checkout_id=None, token=None, customer_id=None
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        # Raise error when trying to attach a user to a checkout
        # that is already owned by another user.
        if checkout.user_id:
            raise PermissionDenied(
                message=(
                    "You cannot reassign a checkout that is already attached to a "
                    "user."
                )
            )

        if customer_id:
            requestor = get_user_or_app_from_context(info.context)
            if not requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
                raise PermissionDenied(
                    permissions=[AccountPermissions.IMPERSONATE_USER]
                )
            customer = cls.get_node_or_error(info, customer_id, only_type="User")
        elif info.context.user.is_anonymous:
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

        info.context.plugins.checkout_updated(checkout)
        return CheckoutCustomerAttach(checkout=checkout)
