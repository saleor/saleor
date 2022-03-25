import graphene
from django.core.exceptions import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import Checkout
from .utils import get_checkout_by_token


class CheckoutEmailUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        email = graphene.String(required=True, description="email.")

    class Meta:
        description = "Updates email address in the existing checkout object."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @staticmethod
    def clean_email(email):
        if not email:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "This field cannot be blank.",
                        code=CheckoutErrorCode.REQUIRED.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, email, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        cls.clean_email(email)

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        checkout.email = email
        cls.clean_instance(info, checkout)
        checkout.save(update_fields=["email", "last_change"])
        info.context.plugins.checkout_updated(checkout)
        return CheckoutEmailUpdate(checkout=checkout)
