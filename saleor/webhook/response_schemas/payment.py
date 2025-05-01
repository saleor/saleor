from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, JsonValue, field_validator

from ...graphql.core.utils import str_to_enum
from ...payment import TokenizedPaymentFlow
from .annotations import DefaultIfNone, OnErrorSkip

TokenizedPaymentFlowEnum = Enum(  # type: ignore[misc]
    "TokenizedPaymentFlowEnum",
    [(str_to_enum(value), value) for value, _ in TokenizedPaymentFlow.CHOICES],
)


class CreditCardInfoSchema(BaseModel):
    brand: Annotated[str, Field(description="Brand of the credit card.")]
    last_digits: Annotated[str, Field(description="Last 4 digits of the credit card.")]
    exp_year: Annotated[int, Field(description="Expiration year of the credit card.")]
    exp_month: Annotated[int, Field(description="Expiration month of the credit card.")]
    first_digits: Annotated[
        DefaultIfNone[str],
        Field(
            description="First 6 digits of the credit card.",
            default=None,
        ),
    ]


class StoredPaymentMethodSchema(BaseModel):
    id: Annotated[str, Field(description="ID of stored payment method.")]
    supported_payment_flows: Annotated[
        DefaultIfNone[list[Literal[TokenizedPaymentFlowEnum.INTERACTIVE.name,]]],
        Field(
            validation_alias="supportedPaymentFlows",
            description="Supported flows that can be performed with this payment method.",
            default_factory=list,
        ),
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
        DefaultIfNone[OnErrorSkip[CreditCardInfoSchema]],
        Field(
            description="Credit card information.",
            default=None,
        ),
    ]

    @field_validator("supported_payment_flows", mode="after")
    @classmethod
    def clean_supported_payment_flows(
        cls, supported_payment_flows: list[str] | None
    ) -> list[str] | None:
        return (
            [flow.lower() for flow in supported_payment_flows]
            if supported_payment_flows
            else supported_payment_flows
        )


class ListStoredPaymentMethodsSchema(BaseModel):
    payment_methods: Annotated[
        DefaultIfNone[list[OnErrorSkip[StoredPaymentMethodSchema]]],
        Field(
            validation_alias="paymentMethods",
            default_factory=list,
            description="List of stored payment methods.",
        ),
    ]
