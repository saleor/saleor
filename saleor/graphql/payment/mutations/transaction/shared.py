import graphene
from django.core.exceptions import ValidationError

from .....payment import PaymentMethodType
from .....payment.error_codes import (
    TransactionCreateErrorCode,
    TransactionEventReportErrorCode,
    TransactionUpdateErrorCode,
)
from .....payment.interface import PaymentMethodDetails
from ....core.descriptions import ADDED_IN_322
from ....core.types.base import BaseInputObjectType
from ....core.validators import validate_one_of_args_is_in_mutation


class CardPaymentMethodDetailsInput(BaseInputObjectType):
    name = graphene.String(
        description="Name of the payment method used for the transaction. Max length is 256 characters.",
        required=True,
    )
    brand = graphene.String(
        description="Brand of the payment method used for the transaction. Max length is 40 characters.",
        required=False,
    )
    first_digits = graphene.String(
        description="First digits of the card used for the transaction. Max length is 4 characters.",
        required=False,
    )
    last_digits = graphene.String(
        description="Last digits of the card used for the transaction. Max length is 4 characters.",
        required=False,
    )
    exp_month = graphene.Int(
        description="Expiration month of the card used for the transaction. Value must be between 1 and 12.",
        required=False,
    )
    exp_year = graphene.Int(
        description="Expiration year of the card used for the transaction. Value must be between 2000 and 9999.",
        required=False,
    )


class OtherPaymentMethodDetailsInput(BaseInputObjectType):
    name = graphene.String(
        description="Name of the payment method used for the transaction.",
        required=True,
    )


class PaymentMethodDetailsInput(BaseInputObjectType):
    card = graphene.Field(
        CardPaymentMethodDetailsInput,
        required=False,
        description="Details of the card payment method used for the transaction.",
    )
    other = graphene.Field(
        OtherPaymentMethodDetailsInput,
        required=False,
        description="Details of the non-card payment method used for this transaction.",
    )

    class Meta:
        description = (
            "Details of the payment method used for the transaction. "
            "One of `card` or `other` is required." + ADDED_IN_322
        )


def validate_card_payment_method_details_input(
    card_method_details_input: CardPaymentMethodDetailsInput,
    error_code_class: type[TransactionEventReportErrorCode]
    | type[TransactionCreateErrorCode]
    | type[TransactionUpdateErrorCode],
):
    errors = []
    if len(card_method_details_input.name) > 256:
        errors.append(
            {
                "name": ValidationError(
                    "The `name` field must be less than 256 characters.",
                    code=error_code_class.INVALID.value,
                )
            }
        )

    if card_method_details_input.brand and len(card_method_details_input.brand) > 40:
        errors.append(
            {
                "brand": ValidationError(
                    "The `brand` field must be less than 40 characters.",
                    code=error_code_class.INVALID.value,
                )
            }
        )
    if (
        card_method_details_input.first_digits
        and len(card_method_details_input.first_digits) > 4
    ):
        errors.append(
            {
                "first_digits": ValidationError(
                    "The `firstDigits` field must be less than 4 characters.",
                    code=error_code_class.INVALID.value,
                )
            }
        )
    if (
        card_method_details_input.last_digits
        and len(card_method_details_input.last_digits) > 4
    ):
        errors.append(
            {
                "last_digits": ValidationError(
                    "The `lastDigits` field must be less than 4 characters.",
                    code=error_code_class.INVALID.value,
                )
            }
        )
    if card_method_details_input.exp_month and (
        card_method_details_input.exp_month < 1
        or card_method_details_input.exp_month > 12
    ):
        errors.append(
            {
                "exp_month": ValidationError(
                    "The `expMonth` field must be between 1 and 12.",
                    code=error_code_class.INVALID.value,
                )
            }
        )
    if card_method_details_input.exp_year and (
        card_method_details_input.exp_year < 2000
        or card_method_details_input.exp_year > 9999
    ):
        errors.append(
            {
                "exp_year": ValidationError(
                    "The `expYear` field must be between 2000 and 9999.",
                    code=error_code_class.INVALID.value,
                )
            }
        )
    return errors


def validate_payment_method_details_input(
    payment_method_details_input: PaymentMethodDetailsInput,
    error_code_class: type[TransactionEventReportErrorCode]
    | type[TransactionCreateErrorCode]
    | type[TransactionUpdateErrorCode],
):
    if (
        payment_method_details_input.card is None
        and payment_method_details_input.other is None
    ):
        raise ValidationError(
            {
                "payment_method_details": ValidationError(
                    "One of `card` or `other` is required.",
                    code=error_code_class.INVALID.value,
                )
            }
        )
    try:
        validate_one_of_args_is_in_mutation(
            "card",
            payment_method_details_input.card,
            "other",
            payment_method_details_input.other,
        )
    except ValidationError as e:
        e.code = error_code_class.INVALID.value
        raise ValidationError({"payment_method_details": e}) from e

    errors = []

    if payment_method_details_input.card:
        errors.extend(
            validate_card_payment_method_details_input(
                payment_method_details_input.card, error_code_class
            )
        )
    elif payment_method_details_input.other:
        if len(payment_method_details_input.other.name) > 256:
            errors.append(
                {
                    "name": ValidationError(
                        "The `name` field must be less than 256 characters.",
                        code=error_code_class.INVALID.value,
                    )
                }
            )

    if errors:
        raise ValidationError({"payment_method_details": errors})


def get_payment_method_details(
    payment_method_details_input: PaymentMethodDetailsInput | None,
) -> PaymentMethodDetails | None:
    """Get the payment method details dataclass from the input."""

    if not payment_method_details_input:
        return None

    payment_details_data: PaymentMethodDetails | None = None
    if payment_method_details_input.card:
        card_details: CardPaymentMethodDetailsInput = payment_method_details_input.card

        payment_details_data = PaymentMethodDetails(
            type=PaymentMethodType.CARD,
            name=card_details.name,
            brand=card_details.brand,
            first_digits=card_details.first_digits,
            last_digits=card_details.last_digits,
            exp_month=card_details.exp_month,
            exp_year=card_details.exp_year,
        )
    elif payment_method_details_input.other:
        other_details: OtherPaymentMethodDetailsInput = (
            payment_method_details_input.other
        )
        payment_details_data = PaymentMethodDetails(
            type=PaymentMethodType.OTHER,
            name=other_details.name,
        )

    return payment_details_data
