import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal

from django.conf import settings
from django.utils import timezone
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    JsonValue,
    field_validator,
)

from ...graphql.core.utils import str_to_enum
from ...payment import (
    OPTIONAL_PSP_REFERENCE_EVENTS,
    TransactionAction,
    TransactionEventType,
)
from .utils.annotations import DatetimeUTC, DefaultIfNone, OnErrorSkipLiteral

logger = logging.getLogger(__name__)


TransactionActionEnum = Enum(  # type: ignore[misc]
    "TransactionActionEnum",
    [(str_to_enum(value), value) for value, _ in TransactionAction.CHOICES],
)


class TransactionBaseSchema(BaseModel):
    psp_reference: Annotated[
        DefaultIfNone[str],
        Field(
            validation_alias="pspReference",
            default=None,
            description=(
                "Psp reference received from payment provider. Optional for the following results: "
                + ", ".join([event.upper() for event in OPTIONAL_PSP_REFERENCE_EVENTS])
            ),
        ),
    ]
    amount: Annotated[
        DefaultIfNone[Decimal],
        Field(
            description="Decimal amount of the processed action",
            default=None,
        ),
    ]
    time: Annotated[
        DefaultIfNone[DatetimeUTC],
        Field(
            description="Time of the action in ISO 8601 format",
            default_factory=timezone.now,
        ),
    ]
    external_url: Annotated[
        DefaultIfNone[HttpUrl],
        Field(
            validation_alias="externalUrl",
            description="External url with action details",
            default="",
        ),
    ]
    message: Annotated[
        DefaultIfNone[str],
        Field(
            description="Message related to the action. The maximum length is 512 characters; any text exceeding this limit will be truncated",
            default="",
        ),
    ]
    actions: (  # type: ignore[name-defined]
        Annotated[
            list[
                OnErrorSkipLiteral[
                    Literal[
                        TransactionActionEnum.CHARGE.name,
                        TransactionActionEnum.REFUND.name,
                        TransactionActionEnum.CANCEL.name,
                    ]
                ]
            ],
            Field(description="List of actions available for the transaction."),
        ]
        | None
    ) = None
    result: Annotated[
        DefaultIfNone[str],
        Field(description="Result of the action"),
    ]

    @field_validator("amount", mode="after")
    @classmethod
    def clean_amount(cls, amount: Decimal | None) -> Decimal | None:
        if amount is None:
            return None
        amount = amount.quantize(Decimal(10) ** (-settings.DEFAULT_DECIMAL_PLACES))
        return amount

    @field_validator("time", mode="before")
    @classmethod
    def clean_time(cls, time: Any) -> datetime | None:
        # pydantic do not support all ISO 8601 formats so in case of string
        # we need to parse it manually; different types are handled by pydantic
        if isinstance(time, str):
            try:
                time = datetime.fromisoformat(time)
            except ValueError as e:
                raise ValueError(
                    "Invalid value for field 'time': {time}. Expected ISO 8601 format."
                ) from e

        return time

    @field_validator("message", mode="before")
    @classmethod
    def clean_message(cls, value: Any):
        from ...payment.utils import (
            TRANSACTION_EVENT_MSG_MAX_LENGTH,
            truncate_transaction_event_message,
        )

        message = value or ""
        try:
            message = str(message)
        except (UnicodeEncodeError, TypeError, ValueError):
            invalid_err_msg = "Incorrect value for field: %s in response of transaction action webhook."
            logger.warning(invalid_err_msg, "message")
            message = ""

        if message and len(message) > TRANSACTION_EVENT_MSG_MAX_LENGTH:
            message = truncate_transaction_event_message(message)
            field_limit_exceeded_msg = (
                "Value for field: %s in response of transaction action webhook "
                "exceeds the character field limit. Message has been truncated."
            )
            logger.warning(field_limit_exceeded_msg, "message")

        return message

    @field_validator("actions", mode="after")
    @classmethod
    def clean_actions(cls, actions: list[str] | None) -> list[str] | None:
        return [action.lower() for action in actions] if actions else actions

    @field_validator("result", mode="after")
    @classmethod
    def clean_result(cls, result: str | None) -> str | None:
        if result is None:
            return None
        return result.lower()


class TransactionAsyncSchema(BaseModel):
    psp_reference: Annotated[
        str,
        Field(
            validation_alias="pspReference",
            description=("Psp reference received from payment provider."),
        ),
    ]
    actions: (  # type: ignore[name-defined]
        Annotated[
            list[
                OnErrorSkipLiteral[
                    Literal[
                        TransactionActionEnum.CHARGE.name,
                        TransactionActionEnum.REFUND.name,
                        TransactionActionEnum.CANCEL.name,
                    ]
                ]
            ],
            Field(description="List of actions available for the transaction."),
        ]
        | None
    ) = None


class TransactionSyncFailureSchema(TransactionBaseSchema):
    psp_reference: Annotated[
        DefaultIfNone[str],
        Field(
            validation_alias="pspReference",
            default=None,
            description=("Psp reference received from payment provider."),
        ),
    ]


class TransactionSyncSuccessSchema(TransactionBaseSchema):
    psp_reference: Annotated[
        str,
        Field(
            validation_alias="pspReference",
            description=("Psp reference received from payment provider."),
        ),
    ]


TransactionEventTypeEnum = Enum(  # type: ignore[misc]
    "TransactionEventTypeEnum",
    [(str_to_enum(value), value) for value, _ in TransactionEventType.CHOICES],
)


class TransactionChargeRequestedAsyncSchema(TransactionAsyncSchema):
    pass


class TransactionChargeRequestedSyncSuccessSchema(TransactionSyncSuccessSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[TransactionEventTypeEnum.CHARGE_SUCCESS.name,],
        Field(description="Result of the action"),
    ]


class TransactionChargeRequestedSyncFailureSchema(TransactionSyncFailureSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[TransactionEventTypeEnum.CHARGE_FAILURE.name,],
        Field(description="Result of the action"),
    ]


class TransactionCancelRequestedAsyncSchema(TransactionAsyncSchema):
    pass


class TransactionCancelRequestedSyncSuccessSchema(TransactionSyncSuccessSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[TransactionEventTypeEnum.CANCEL_SUCCESS.name,],
        Field(description="Result of the action"),
    ]


class TransactionCancelRequestedSyncFailureSchema(TransactionSyncFailureSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[TransactionEventTypeEnum.CANCEL_FAILURE.name,],
        Field(description="Result of the action"),
    ]


class TransactionRefundRequestedAsyncSchema(TransactionAsyncSchema):
    pass


class TransactionRefundRequestedSyncSuccessSchema(TransactionSyncSuccessSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[TransactionEventTypeEnum.REFUND_SUCCESS.name,],
        Field(description="Result of the action"),
    ]


class TransactionRefundRequestedSyncFailureSchema(TransactionSyncFailureSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[TransactionEventTypeEnum.REFUND_FAILURE.name,],
        Field(description="Result of the action"),
    ]


class TransactionSessionBaseSchema(TransactionBaseSchema):
    data: Annotated[
        DefaultIfNone[JsonValue],
        Field(
            description="The JSON data that will be returned to storefront",
            default=None,
        ),
    ]


class TransactionSessionFailureSchema(TransactionSessionBaseSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.AUTHORIZATION_FAILURE.name,
            TransactionEventTypeEnum.CHARGE_FAILURE.name,
        ],
        Field(description="Result of the action"),
    ]
    psp_reference: Annotated[
        DefaultIfNone[str],
        Field(
            validation_alias="pspReference",
            default=None,
            description=("Psp reference received from payment provider."),
        ),
    ]


class TransactionSessionActionRequiredSchema(TransactionSessionBaseSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.AUTHORIZATION_ACTION_REQUIRED.name,
            TransactionEventTypeEnum.CHARGE_ACTION_REQUIRED.name,
        ],
        Field(description="Result of the action"),
    ]
    psp_reference: Annotated[
        DefaultIfNone[str],
        Field(
            validation_alias="pspReference",
            default=None,
            description=("Psp reference received from payment provider."),
        ),
    ]


class TransactionSessionSuccessSchema(TransactionSessionBaseSchema):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
            TransactionEventTypeEnum.CHARGE_SUCCESS.name,
            TransactionEventTypeEnum.AUTHORIZATION_REQUEST.name,
            TransactionEventTypeEnum.CHARGE_REQUEST.name,
        ],
        Field(description="Result of the action"),
    ]
    psp_reference: Annotated[
        str,
        Field(
            validation_alias="pspReference",
            description=("Psp reference received from payment provider."),
        ),
    ]


class PaymentGatewayInitializeSessionSchema(BaseModel):
    data: JsonValue
