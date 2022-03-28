import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.enums import LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import Checkout
from .utils import get_checkout_by_token


class CheckoutLanguageCodeUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
        )
        token = UUID(description="Checkout token.", required=False)
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="New language code."
        )

    class Meta:
        description = "Update language code in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, language_code, checkout_id=None, token=None):
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

        checkout.language_code = language_code
        checkout.save(update_fields=["language_code", "last_change"])
        info.context.plugins.checkout_updated(checkout)
        return CheckoutLanguageCodeUpdate(checkout=checkout)
