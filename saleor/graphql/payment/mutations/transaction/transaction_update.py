from typing import TYPE_CHECKING, Optional

import graphene
from django.core.exceptions import ValidationError

from .....app.models import App
from .....core.exceptions import PermissionDenied
from .....order.events import transaction_event as order_transaction_event
from .....payment import models as payment_models
from .....payment.error_codes import (
    TransactionCreateErrorCode,
    TransactionUpdateErrorCode,
)
from .....payment.interface import PaymentMethodDetails
from .....payment.transaction_item_calculations import (
    calculate_transaction_amount_based_on_events,
    recalculate_transaction_amounts,
)
from .....payment.utils import (
    create_manual_adjustment_events,
    process_order_or_checkout_with_transaction,
    update_transaction_item_with_payment_method_details,
)
from .....permission.auth_filters import AuthorizationFilters
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.scalars import UUID
from ....core.types import common as common_types
from ....core.validators import validate_one_of_args_is_in_mutation
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import TransactionItem
from ...utils import check_if_requestor_has_access
from .shared import get_payment_method_details, validate_payment_method_details_input
from .transaction_create import (
    TransactionCreate,
    TransactionCreateInput,
    TransactionEventInput,
)
from .utils import get_transaction_item

if TYPE_CHECKING:
    from .....account.models import User


class TransactionUpdateInput(TransactionCreateInput):
    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionUpdate(TransactionCreate):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description=(
                "The ID of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        token = UUID(
            description=(
                "The token of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        transaction = TransactionUpdateInput(
            description="Input data required to create a new transaction object.",
        )
        transaction_event = TransactionEventInput(
            description="Data that defines a transaction transaction."
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Update transaction."
            + "\n\nRequires the following permissions: "
            + f"{AuthorizationFilters.OWNER.name} "
            + f"and {PaymentPermissions.HANDLE_PAYMENTS.name} for apps, "
            f"{PaymentPermissions.HANDLE_PAYMENTS.name} for staff users. "
            f"Staff user cannot update a transaction that is owned by the app."
        )
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionUpdateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)
        object_type = TransactionItem

    @classmethod
    def check_can_update(
        cls,
        transaction: payment_models.TransactionItem,
        user: Optional["User"],
        app: Optional["App"],
    ):
        if not check_if_requestor_has_access(
            transaction=transaction, user=user, app=app
        ):
            raise PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    PaymentPermissions.HANDLE_PAYMENTS,
                ]
            )

    @classmethod
    def validate_transaction_input(
        cls, instance: payment_models.TransactionItem, transaction_data
    ):
        currency = instance.currency
        if transaction_data.get("available_actions") is not None:
            transaction_data["available_actions"] = list(
                set(transaction_data.get("available_actions", []))
            )

        cls.validate_money_input(
            transaction_data,
            currency,
            TransactionUpdateErrorCode.INCORRECT_CURRENCY.value,
        )
        cls.validate_metadata_keys(
            transaction_data.get("metadata", []),
            field_name="metadata",
            error_code=TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_metadata_keys(
            transaction_data.get("private_metadata", []),
            field_name="privateMetadata",
            error_code=TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_external_url(
            transaction_data.get("external_url"),
            error_code=TransactionCreateErrorCode.INVALID.value,
        )
        if payment_method_details := transaction_data.get("payment_method_details"):
            validate_payment_method_details_input(
                payment_method_details, TransactionUpdateErrorCode
            )

    @classmethod
    def update_transaction(
        cls,
        instance: payment_models.TransactionItem,
        transaction_data: dict,
        money_data: dict,
        user: Optional["User"],
        app: Optional["App"],
        payment_details_data: PaymentMethodDetails | None = None,
    ):
        psp_reference = transaction_data.get("psp_reference")
        if psp_reference and instance.psp_reference != psp_reference:
            if payment_models.TransactionItem.objects.filter(
                psp_reference=psp_reference
            ).exists():
                raise ValidationError(
                    {
                        "transaction": ValidationError(
                            "Transaction with provided `pspReference` already exists.",
                            code=TransactionUpdateErrorCode.UNIQUE.value,
                        )
                    }
                )
        instance = cls.construct_instance(instance, transaction_data)
        if payment_details_data:
            update_transaction_item_with_payment_method_details(
                instance, payment_details_data
            )
        instance.save()
        if money_data:
            calculate_transaction_amount_based_on_events(transaction=instance)
            create_manual_adjustment_events(
                transaction=instance, money_data=money_data, user=user, app=app
            )
            recalculate_transaction_amounts(instance)

    @classmethod
    def assign_app_to_transaction_data_if_missing(
        cls,
        transaction: payment_models.TransactionItem,
        transaction_data: dict,
        app: Optional["App"],
    ):
        """Assign app to transaction if missing.

        TransactionItem created before 3.13, doesn't have a relation to the owner app.
        When app updates a transaction, we need to assign the app to the transaction.
        """
        transaction_has_assigned_app = transaction.app_id or transaction.app_identifier
        if app and not transaction.user_id and not transaction_has_assigned_app:
            transaction_data["app"] = app
            transaction_data["app_identifier"] = app.identifier

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        token=None,
        id=None,
        transaction=None,
        transaction_event=None,
    ):
        validate_one_of_args_is_in_mutation("id", id, "token", token)
        instance = get_transaction_item(id, token)
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()

        cls.check_can_update(
            transaction=instance,
            user=user if user and user.is_authenticated else None,
            app=app,
        )
        money_data = {}
        previous_authorized_value = instance.authorized_value
        previous_charged_value = instance.charged_value
        previous_refunded_value = instance.refunded_value

        if transaction:
            cls.validate_transaction_input(instance, transaction)
            cls.assign_app_to_transaction_data_if_missing(instance, transaction, app)
            cls.cleanup_and_update_metadata_data(
                instance,
                transaction.pop("metadata", None),
                transaction.pop("private_metadata", None),
            )
            money_data = cls.get_money_data_from_input(transaction, instance.currency)
            payment_details_data: PaymentMethodDetails | None = None
            if payment_method_details := transaction.pop(
                "payment_method_details", None
            ):
                payment_details_data = get_payment_method_details(
                    payment_method_details
                )
            cls.update_transaction(
                instance,
                transaction,
                money_data,
                user,
                app,
                payment_details_data=payment_details_data,
            )

        if transaction_event:
            cls.create_transaction_event(transaction_event, instance, user, app)
            if instance.order:
                order_transaction_event(
                    order=instance.order,
                    user=user,
                    app=app,
                    reference=transaction_event.get("psp_reference"),
                    message=transaction_event.get("message", ""),
                )

        process_order_or_checkout_with_transaction(
            instance,
            manager,
            user,
            app,
            previous_authorized_value,
            previous_charged_value,
            previous_refunded_value,
        )

        return TransactionUpdate(transaction=instance)
