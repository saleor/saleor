import graphene
from django.core.exceptions import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Checkout
from .utils import get_checkout


class CheckoutEmailUpdate(BaseMutation):
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
    def perform_mutation(
        cls, _root, info, email, checkout_id=None, token=None, id=None
    ):
        cls.clean_email(email)

        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=CheckoutErrorCode,
        )

        checkout.email = email
        cls.clean_instance(info, checkout)
        checkout.save(update_fields=["email", "last_change"])
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.checkout_updated, checkout)
        return CheckoutEmailUpdate(checkout=checkout)
