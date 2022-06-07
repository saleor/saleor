import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.enums import LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ..types import Checkout
from .utils import get_checkout


class CheckoutLanguageCodeUpdate(BaseMutation):
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
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="New language code."
        )

    class Meta:
        description = "Update language code in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls, _root, info, language_code, checkout_id=None, token=None, id=None
    ):
        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=CheckoutErrorCode,
        )

        checkout.language_code = language_code
        checkout.save(update_fields=["language_code", "last_change"])
        info.context.plugins.checkout_updated(checkout)
        return CheckoutLanguageCodeUpdate(checkout=checkout)
