from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from ...app.models import App
from ...graphql.core.utils import str_to_enum
from ...payment import TokenizedPaymentFlow
from ...payment.interface import (
    PaymentGatewayInitializeTokenizationResult,
    PaymentMethodTokenizationResult,
    StoredPaymentMethodRequestDeleteResult,
)
from .utils.annotations import (
    DefaultIfNone,
    EnumByName,
    JSONValue,
    OnErrorDefault,
    OnErrorSkip,
)
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
        DefaultIfNone[JSONValue],
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


class StoredPaymentMethodDeleteRequestedSchema(BaseModel):
    result: Annotated[
        EnumByName[StoredPaymentMethodRequestDeleteResult],
        Field(
            description="Result of the request to delete the stored payment method.",
        ),
    ]
    error: Annotated[
        str | None,
        Field(
            description="Error message if the request to delete the stored payment method failed that will be passed to the frontend.",
            default=None,
        ),
    ]


class PaymentGatewayInitializeTokenizationSessionSchema(BaseModel):
    result: Annotated[
        EnumByName[PaymentGatewayInitializeTokenizationResult],
        Field(
            description="Result of the payment gateway initialization.",
        ),
    ]
    data: Annotated[
        DefaultIfNone[JSONValue],
        Field(
            default=None,
            description="A data required to finalize the initialization.",
        ),
    ]
    error: Annotated[
        str | None,
        Field(
            description="Error message that will be passed to the frontend.",
            default=None,
        ),
    ]


def clean_id(payment_method_id: str, info: ValidationInfo) -> str:
    from ..transport.utils import to_payment_app_id

    app: App | None = info.context.get("app", None) if info.context else None
    if not app:
        raise RuntimeError("Missing app in context")
    return to_payment_app_id(app, payment_method_id)


def clean_result(result: str):
    return PaymentMethodTokenizationResult[result]


class PaymentMethodTokenizationSuccessSchema(BaseModel):
    id: Annotated[str, Field(description="ID of the payment method.")]
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
            PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED.name,
        ],
        Field(
            description="Result of the payment method tokenization.",
        ),
        AfterValidator(clean_result),
    ]
    data: Annotated[
        DefaultIfNone[JSONValue],
        Field(
            description="A data passes to the client.",
            default=None,
        ),
    ]

    @model_validator(mode="after")
    def clean_id(self, info: ValidationInfo):
        payment_method_id = self.id
        self.id = clean_id(payment_method_id, info)
        return self


class PaymentMethodTokenizationPendingSchema(BaseModel):
    id: Annotated[
        str | None, Field(description="ID of the payment method.", default=None)
    ]
    result: Annotated[  # type: ignore[name-defined]
        Literal[PaymentMethodTokenizationResult.PENDING.name],
        Field(
            description="Result of the payment method tokenization.",
        ),
        AfterValidator(clean_result),
    ]
    data: Annotated[
        DefaultIfNone[JSONValue],
        Field(
            description="A data passes to the client.",
            default=None,
        ),
    ]

    @model_validator(mode="after")
    def clean_id(self, info: ValidationInfo):
        payment_method_id = self.id
        if payment_method_id is None:
            return self
        self.id = clean_id(payment_method_id, info)
        return self


class PaymentMethodTokenizationFailedSchema(BaseModel):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
            PaymentMethodTokenizationResult.FAILED_TO_DELIVER.name,
        ],
        Field(
            description="Result of the payment method tokenization.",
        ),
        AfterValidator(clean_result),
    ]
    error: Annotated[
        str | None,
        Field(
            description="Error message that will be passed to the frontend.",
            default=None,
        ),
    ]
