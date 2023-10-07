import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Union, cast

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Model

from .....checkout import models as checkout_models
from .....checkout.actions import transaction_amounts_for_checkout_updated
from .....order import OrderStatus
from .....order import models as order_models
from .....order.actions import order_transaction_updated
from .....order.events import transaction_event as order_transaction_event
from .....order.fetch import fetch_order_info
from .....order.search import update_order_search_vector
from .....order.utils import updates_amounts_for_order
from .....payment import TransactionEventType
from .....payment import models as payment_models
from .....payment.error_codes import TransactionCreateErrorCode
from .....payment.transaction_item_calculations import recalculate_transaction_amounts
from .....payment.utils import create_manual_adjustment_events
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_34, ADDED_IN_313, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType
from ....core.types import common as common_types
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import TransactionActionEnum
from ...types import TransactionItem
from ...utils import metadata_contains_empty_key
from ..payment.payment_check_balance import MoneyInput


class TransactionCreateInput(BaseInputObjectType):
    name = graphene.String(
        description="Payment name of the transaction." + ADDED_IN_313
    )
    message = graphene.String(
        description="The message of the transaction." + ADDED_IN_313
    )

    psp_reference = graphene.String(
        description=("PSP Reference of the transaction. " + ADDED_IN_313)
    )
    available_actions = graphene.List(
        graphene.NonNull(TransactionActionEnum),
        description="List of all possible actions for the transaction",
    )
    amount_authorized = MoneyInput(description="Amount authorized by this transaction.")
    amount_charged = MoneyInput(description="Amount charged by this transaction.")
    amount_refunded = MoneyInput(description="Amount refunded by this transaction.")

    amount_canceled = MoneyInput(
        description="Amount canceled by this transaction." + ADDED_IN_313
    )

    metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Payment public metadata.",
        required=False,
    )
    private_metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Payment private metadata.",
        required=False,
    )
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction event details." + ADDED_IN_313
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionEventInput(BaseInputObjectType):
    psp_reference = graphene.String(
        description=("PSP Reference related to this action." + ADDED_IN_313)
    )

    message = graphene.String(
        description="The message related to the event." + ADDED_IN_313
    )

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
        description = (
            "Create transaction for checkout or order." + ADDED_IN_34 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionCreateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def validate_external_url(cls, external_url: Optional[str], error_code: str):
        if external_url is None:
            return
        validator = URLValidator()
        try:
            validator(external_url)
        except ValidationError:
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        "Invalid format of `externalUrl`.", code=error_code
                    )
                }
            )

    @classmethod
    def validate_metadata_keys(  # type: ignore[override]
        cls, metadata_list: List[dict], field_name, error_code
    ):
        if metadata_contains_empty_key(metadata_list):
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        f"{field_name} key cannot be empty.",
                        code=error_code,
                    )
                }
            )

    @classmethod
    def get_money_data_from_input(cls, cleaned_data: dict) -> Dict[str, Decimal]:
        money_data = {}
        if amount_authorized := cleaned_data.pop("amount_authorized", None):
            money_data["authorized_value"] = amount_authorized["amount"]
        if amount_charged := cleaned_data.pop("amount_charged", None):
            money_data["charged_value"] = amount_charged["amount"]
        if amount_refunded := cleaned_data.pop("amount_refunded", None):
            money_data["refunded_value"] = amount_refunded["amount"]

        if amount_canceled := cleaned_data.pop("amount_canceled", None):
            money_data["canceled_value"] = amount_canceled["amount"]
        return money_data

    @classmethod
    def cleanup_metadata_data(cls, cleaned_data: dict):
        if metadata := cleaned_data.pop("metadata", None):
            cleaned_data["metadata"] = {data.key: data.value for data in metadata}
        if private_metadata := cleaned_data.pop("private_metadata", None):
            cleaned_data["private_metadata"] = {
                data.key: data.value for data in private_metadata
            }

    @classmethod
    def validate_instance(
        cls, instance: Model, instance_id
    ) -> Union[checkout_models.Checkout, order_models.Order]:
        """Validate if provided instance is an order or checkout type."""
        if not isinstance(instance, (checkout_models.Checkout, order_models.Order)):
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
        cls, instance: Union[checkout_models.Checkout, order_models.Order], transaction
    ) -> Union[checkout_models.Checkout, order_models.Order]:
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
        return instance

    @classmethod
    def create_transaction(
        cls, transaction_input: dict, user, app, save: bool = True
    ) -> payment_models.TransactionItem:
        cls.cleanup_metadata_data(transaction_input)
        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier
        transaction_input["available_actions"] = list(
            set(transaction_input.get("available_actions", []))
        )
        transaction = payment_models.TransactionItem(
            token=uuid.uuid4(),
            use_old_id=True,
            **transaction_input,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
        )
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
        return transaction.events.create(
            psp_reference=transaction_event_input.get("psp_reference"),
            message=transaction_event_input.get("message", ""),
            transaction=transaction,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
            type=TransactionEventType.INFO,
            currency=transaction.currency,
        )

    @classmethod
    def update_order(
        cls,
        order: order_models.Order,
        money_data: dict,
        update_search_vector: bool = True,
    ) -> None:
        update_fields = []
        if money_data:
            updates_amounts_for_order(order, save=False)
            update_fields.extend(
                [
                    "total_authorized_amount",
                    "total_charged_amount",
                    "authorize_status",
                    "charge_status",
                ]
            )
        if (
            order.channel.automatically_confirm_all_new_orders
            and order.status == OrderStatus.UNCONFIRMED
        ):
            order.status = OrderStatus.UNFULFILLED
            update_fields.append("status")

        if update_search_vector:
            update_order_search_vector(order, save=False)
            update_fields.append(
                "search_vector",
            )

        if update_fields:
            update_fields.append("updated_at")
            order.save(update_fields=update_fields)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id: str,
        transaction: Dict,
        transaction_event=None,
    ):
        order_or_checkout_instance = cls.get_node_or_error(info, id)
        order_or_checkout_instance = cls.validate_instance(
            order_or_checkout_instance, id
        )
        order_or_checkout_instance = cls.validate_input(
            order_or_checkout_instance, transaction=transaction
        )
        transaction_data = {**transaction}
        transaction_data["currency"] = order_or_checkout_instance.currency
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
        money_data = cls.get_money_data_from_input(transaction_data)
        new_transaction = cls.create_transaction(transaction_data, user=user, app=app)
        if money_data:
            create_manual_adjustment_events(
                transaction=new_transaction, money_data=money_data, user=user, app=app
            )
            recalculate_transaction_amounts(new_transaction)
        if transaction_data.get("order_id") and money_data:
            order = cast(order_models.Order, new_transaction.order)
            cls.update_order(order, money_data, update_search_vector=True)

            order_info = fetch_order_info(order)
            order_transaction_updated(
                order_info=order_info,
                transaction_item=new_transaction,
                manager=manager,
                user=user,
                app=app,
                previous_authorized_value=Decimal(0),
                previous_charged_value=Decimal(0),
                previous_refunded_value=Decimal(0),
            )
        if transaction_data.get("checkout_id") and money_data:
            transaction_amounts_for_checkout_updated(new_transaction, manager)

        if transaction_event:
            cls.create_transaction_event(transaction_event, new_transaction, user, app)
        return TransactionCreate(transaction=new_transaction)
