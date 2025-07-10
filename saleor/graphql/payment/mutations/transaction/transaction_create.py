import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Model

from .....checkout import models as checkout_models
from .....core.prices import quantize_price
from .....order import models as order_models
from .....order.events import transaction_event as order_transaction_event
from .....payment import TransactionEventType
from .....payment import models as payment_models
from .....payment.error_codes import TransactionCreateErrorCode
from .....payment.interface import PaymentMethodDetails
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....payment.utils import (
    create_manual_adjustment_events,
    process_order_or_checkout_with_transaction,
    truncate_transaction_event_message,
    update_transaction_item_with_payment_method_details,
)
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_322
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType
from ....core.types import common as common_types
from ....meta.inputs import MetadataInput, MetadataInputDescription
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import TransactionActionEnum
from ...types import TransactionItem
from ...utils import deprecated_metadata_contains_empty_key
from ..payment.payment_check_balance import MoneyInput
from .shared import (
    PaymentMethodDetailsInput,
    get_payment_method_details,
    validate_payment_method_details_input,
)

if TYPE_CHECKING:
    pass


class TransactionCreateInput(BaseInputObjectType):
    name = graphene.String(description="Payment name of the transaction.")
    message = graphene.String(description="The message of the transaction.")

    psp_reference = graphene.String(description=("PSP Reference of the transaction. "))
    available_actions = graphene.List(
        graphene.NonNull(TransactionActionEnum),
        description="List of all possible actions for the transaction",
    )
    amount_authorized = MoneyInput(description="Amount authorized by this transaction.")
    amount_charged = MoneyInput(description="Amount charged by this transaction.")
    amount_refunded = MoneyInput(description="Amount refunded by this transaction.")

    amount_canceled = MoneyInput(description="Amount canceled by this transaction.")

    metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Payment public metadata. "
        f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}",
        required=False,
    )
    private_metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Payment private metadata. "
        f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}",
        required=False,
    )
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction event details."
        )
    )
    payment_method_details = PaymentMethodDetailsInput(
        description="Details of the payment method used for the transaction."
        + ADDED_IN_322,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionEventInput(BaseInputObjectType):
    psp_reference = graphene.String(
        description=("PSP Reference related to this action.")
    )

    message = graphene.String(description="The message related to the event.")

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionCreate(BaseMutation):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description="The ID of the checkout or order.",
            required=True,
        )
        transaction = TransactionCreateInput(
            required=True,
            description="Input data required to create a new transaction object.",
        )
        transaction_event = TransactionEventInput(
            description="Data that defines a transaction event."
        )

    class Meta:
        description = "Create transaction for checkout or order."
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionCreateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def validate_external_url(cls, external_url: str | None, error_code: str):
        if external_url is None:
            return
        validator = URLValidator()
        try:
            validator(external_url)
        except ValidationError as e:
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        "Invalid format of `externalUrl`.", code=error_code
                    )
                }
            ) from e

    # TODO This should be unified with metadata_manager and MetadataItemCollection
    # EXT-2054
    @classmethod
    def validate_metadata_keys(
        cls, metadata_list: list[dict] | None, field_name, error_code
    ):
        if not metadata_list:
            return
        if deprecated_metadata_contains_empty_key(metadata_list):
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        f"{field_name} key cannot be empty.",
                        code=error_code,
                    )
                }
            )

    @classmethod
    def get_money_data_from_input(
        cls, cleaned_data: dict, currency: str
    ) -> dict[str, Decimal]:
        money_data = {}
        if amount_authorized := cleaned_data.pop("amount_authorized", None):
            money_data["authorized_value"] = quantize_price(
                amount_authorized["amount"], currency
            )
        if amount_charged := cleaned_data.pop("amount_charged", None):
            money_data["charged_value"] = quantize_price(
                amount_charged["amount"], currency
            )
        if amount_refunded := cleaned_data.pop("amount_refunded", None):
            money_data["refunded_value"] = quantize_price(
                amount_refunded["amount"], currency
            )

        if amount_canceled := cleaned_data.pop("amount_canceled", None):
            money_data["canceled_value"] = quantize_price(
                amount_canceled["amount"], currency
            )
        return money_data

    @classmethod
    def cleanup_and_update_metadata_data(
        cls,
        transaction: payment_models.TransactionItem,
        metadata: list | None,
        private_metadata: list | None,
    ):
        if metadata is not None:
            transaction.store_value_in_metadata(
                {data.key: data.value for data in metadata}
            )
        if private_metadata is not None:
            transaction.store_value_in_private_metadata(
                {data.key: data.value for data in private_metadata}
            )

    @classmethod
    def validate_instance(
        cls, instance: Model, instance_id
    ) -> checkout_models.Checkout | order_models.Order:
        """Validate if provided instance is an order or checkout type."""
        if not isinstance(instance, checkout_models.Checkout | order_models.Order):
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Couldn't resolve to Checkout or Order: {instance_id}",
                        code=TransactionCreateErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return instance

    @classmethod
    def validate_money_input(
        cls, transaction_data: dict, currency: str, error_code: str
    ):
        if not transaction_data:
            return
        money_input_fields = [
            "amount_authorized",
            "amount_charged",
            "amount_refunded",
            "amount_canceled",
        ]
        errors = {}
        for money_field_name in money_input_fields:
            field = transaction_data.get(money_field_name)
            if not field:
                continue
            if field["currency"] != currency:
                errors[money_field_name] = ValidationError(
                    f"Currency needs to be the same as for order: {currency}",
                    code=error_code,
                )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def validate_input(
        cls, instance: checkout_models.Checkout | order_models.Order, transaction
    ) -> checkout_models.Checkout | order_models.Order:
        currency = instance.currency

        cls.validate_money_input(
            transaction,
            currency,
            TransactionCreateErrorCode.INCORRECT_CURRENCY.value,
        )
        cls.validate_metadata_keys(
            transaction.get("metadata", []),
            field_name="metadata",
            error_code=TransactionCreateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_metadata_keys(
            transaction.get("private_metadata", []),
            field_name="privateMetadata",
            error_code=TransactionCreateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_external_url(
            transaction.get("external_url"),
            error_code=TransactionCreateErrorCode.INVALID.value,
        )
        if payment_method_details := transaction.get("payment_method_details"):
            validate_payment_method_details_input(
                payment_method_details, TransactionCreateErrorCode
            )

        if "available_actions" in transaction and not transaction["available_actions"]:
            transaction.pop("available_actions")
        return instance

    @classmethod
    def create_transaction(
        cls,
        transaction_input: dict,
        user,
        app,
        save: bool = True,
        payment_details_data: PaymentMethodDetails | None = None,
    ) -> payment_models.TransactionItem:
        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier
        transaction_input["available_actions"] = list(
            set(transaction_input.get("available_actions", []))
        )
        metadata = transaction_input.pop("metadata", None)
        private_metadata = transaction_input.pop("private_metadata", None)
        transaction = payment_models.TransactionItem(
            token=uuid.uuid4(),
            use_old_id=True,
            **transaction_input,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
        )
        if payment_details_data:
            update_transaction_item_with_payment_method_details(
                transaction, payment_details_data
            )
        cls.cleanup_and_update_metadata_data(transaction, metadata, private_metadata)
        if save:
            transaction.save()
        return transaction

    @classmethod
    def create_transaction_event(
        cls,
        transaction_event_input: dict,
        transaction: payment_models.TransactionItem,
        user,
        app,
    ) -> payment_models.TransactionEvent:
        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier
        message = transaction_event_input.get("message") or ""
        return transaction.events.create(
            psp_reference=transaction_event_input.get("psp_reference"),
            message=truncate_transaction_event_message(message),
            transaction=transaction,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
            type=TransactionEventType.INFO,
            currency=transaction.currency,
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id: str,
        transaction: dict,
        transaction_event=None,
    ):
        order_or_checkout_instance = cls.get_node_or_error(info, id)
        order_or_checkout_instance = cls.validate_instance(
            order_or_checkout_instance, id
        )
        order_or_checkout_instance = cls.validate_input(
            order_or_checkout_instance, transaction=transaction
        )
        payment_details_data: PaymentMethodDetails | None = None
        if payment_method_details := transaction.pop("payment_method_details", None):
            payment_details_data = get_payment_method_details(payment_method_details)

        transaction_data = {**transaction}
        currency = order_or_checkout_instance.currency
        transaction_data["currency"] = currency
        app = get_app_promise(info.context).get()
        user = info.context.user
        manager = get_plugin_manager_promise(info.context).get()

        if isinstance(order_or_checkout_instance, checkout_models.Checkout):
            transaction_data["checkout_id"] = order_or_checkout_instance.pk
        else:
            transaction_data["order_id"] = order_or_checkout_instance.pk
            if transaction_event:
                order_transaction_event(
                    order=order_or_checkout_instance,
                    user=user,
                    app=app,
                    reference=transaction_event.get("psp_reference"),
                    message=transaction_event.get("message", ""),
                )
        money_data = cls.get_money_data_from_input(transaction_data, currency)
        new_transaction = cls.create_transaction(
            transaction_data,
            user=user,
            app=app,
            payment_details_data=payment_details_data,
        )
        if money_data:
            create_manual_adjustment_events(
                transaction=new_transaction, money_data=money_data, user=user, app=app
            )
            recalculate_transaction_amounts(new_transaction)
        process_order_or_checkout_with_transaction(
            new_transaction,
            manager,
            user,
            app,
        )

        if transaction_event:
            cls.create_transaction_event(transaction_event, new_transaction, user, app)
        return TransactionCreate(transaction=new_transaction)
