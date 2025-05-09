from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, Field, JsonValue, field_validator

from ...graphql.core.utils import str_to_enum
from ...payment import TokenizedPaymentFlow
from .utils.annotations import DefaultIfNone, OnErrorDefault, OnErrorSkip
from .utils.validators import lower_values

TokenizedPaymentFlowEnum = Enum(  # type: ignore[misc]
    "TokenizedPaymentFlowEnum",
    [(str_to_enum(value), value) for value, _ in TokenizedPaymentFlow.CHOICES],
)


class CreditCardInfoSchema(BaseModel):
    brand: Annotated[str, Field(description="Brand of the credit card.")]
    last_digits: Annotated[
        str,
        Field(
            validation_alias="lastDigits", description="Last digits of the credit card."
        ),
    ]
    exp_year: Annotated[
        int,
        Field(
            validation_alias="expYear",
            description="Expiration year of the credit card.",
        ),
    ]
    exp_month: Annotated[
        int,
        Field(
            validation_alias="expMonth",
            description="Expiration month of the credit card.",
        ),
    ]
    first_digits: Annotated[
        DefaultIfNone[str],
        Field(
            validation_alias="firstDigits",
            description="First digits of the credit card.",
            default=None,
        ),
    ]

    @field_validator("last_digits", "first_digits", mode="before")
    @classmethod
    def clean_digits(cls, value: Any) -> str | None:
        return str(value) if value is not None else None


class StoredPaymentMethodSchema(BaseModel):
    id: Annotated[str, Field(description="ID of stored payment method.")]
    supported_payment_flows: Annotated[  # type: ignore[name-defined]
        DefaultIfNone[list[Literal[TokenizedPaymentFlowEnum.INTERACTIVE.name,]]],
        Field(
            validation_alias="supportedPaymentFlows",
            description="Supported flows that can be performed with this payment method.",
            default_factory=list,
        ),
        AfterValidator(lower_values),
    ]
    type: Annotated[
        str,
        Field(description="Type of stored payment method. For example: Credit Card."),
    ]
    name: Annotated[
        DefaultIfNone[str],
        Field(
            description="Name of the payment method. For example: last 4 digits of credit card, obfuscated email.",
            default=None,
        ),
    ]
    data: Annotated[
        DefaultIfNone[JsonValue],
        Field(
            description="JSON data that will be returned to client.",
            default=None,
        ),
    ]
    credit_card_info: Annotated[
        OnErrorDefault[CreditCardInfoSchema],
        Field(
            validation_alias="creditCardInfo",
            description="Credit card information.",
            default=None,
        ),
    ]


class ListStoredPaymentMethodsSchema(BaseModel):
    payment_methods: Annotated[
        DefaultIfNone[list[OnErrorSkip[StoredPaymentMethodSchema]]],
        Field(
            validation_alias="paymentMethods",
            default_factory=list,
            description="List of stored payment methods.",
        ),
    ]
