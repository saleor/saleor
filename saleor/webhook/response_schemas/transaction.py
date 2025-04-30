import json
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
    Json,
    field_validator,
    model_validator,
)

from ...graphql.core.utils import str_to_enum
from ...payment import (
    OPTIONAL_PSP_REFERENCE_EVENTS,
    TransactionAction,
    TransactionEventType,
)
from .annotations import DatetimeUTC, DefaultIfNone, OnErrorSkipLiteral

logger = logging.getLogger(__name__)


TransactionActionEnum = Enum(  # type: ignore[misc]
    "TransactionActionEnum",
    [(str_to_enum(value), value) for value, _ in TransactionAction.CHOICES],
)


class TransactionResponse(BaseModel):
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
        Decimal, Field(description="Decimal amount of the processed action")
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
        str,
        Field(description="Result of the action"),
    ]

    @model_validator(mode="after")
    def clean_psp_reference(self):
        if not self.psp_reference and self.result not in OPTIONAL_PSP_REFERENCE_EVENTS:
            error_msg = f"Providing `pspReference` is required for {self.result.upper()} action result."
            raise ValueError(error_msg)
        return self

    @field_validator("amount", mode="after")
    @classmethod
    def clean_amount(cls, amount: Decimal) -> Decimal:
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
    def clean_result(cls, result: str) -> str:
        return result.lower()


TransactionEventTypeEnum = Enum(  # type: ignore[misc]
    "TransactionEventTypeEnum",
    [(str_to_enum(value), value) for value, _ in TransactionEventType.CHOICES],
)


class TransactionChargeRequestedResponse(TransactionResponse):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.CHARGE_SUCCESS.name,
            TransactionEventTypeEnum.CHARGE_FAILURE.name,
        ],
        Field(description="Result of the action"),
    ]


class TransactionCancelRequestedResponse(TransactionResponse):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.CANCEL_SUCCESS.name,
            TransactionEventTypeEnum.CANCEL_FAILURE.name,
        ],
        Field(description="Result of the action"),
    ]


class TransactionRefundRequestedResponse(TransactionResponse):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.REFUND_SUCCESS.name,
            TransactionEventTypeEnum.REFUND_FAILURE.name,
        ],
        Field(description="Result of the action"),
    ]


class TransactionSessionResponse(TransactionResponse):
    result: Annotated[  # type: ignore[name-defined]
        Literal[
            TransactionEventTypeEnum.AUTHORIZATION_SUCCESS.name,
            TransactionEventTypeEnum.AUTHORIZATION_FAILURE.name,
            TransactionEventTypeEnum.AUTHORIZATION_ACTION_REQUIRED.name,
            TransactionEventTypeEnum.AUTHORIZATION_REQUEST.name,
            TransactionEventTypeEnum.CHARGE_SUCCESS.name,
            TransactionEventTypeEnum.CHARGE_FAILURE.name,
            TransactionEventTypeEnum.CHARGE_ACTION_REQUIRED.name,
            TransactionEventTypeEnum.CHARGE_REQUEST.name,
        ],
        Field(description="Result of the action"),
    ]
    data: Annotated[
        DefaultIfNone[Json],
        Field(
            description="The JSON data that will be returned to storefront",
            default=None,
        ),
    ]

    @field_validator("data", mode="before")
    @classmethod
    def validate_data(cls, value: Any) -> str:
        # parse input value to raw JSON string
        try:
            return json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Invalid value for field 'data': {value}. Expected JSON format."
            ) from e
