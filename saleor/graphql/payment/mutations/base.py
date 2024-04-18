from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

from django.conf import settings
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....checkout import models as checkout_models
from ....checkout.calculations import fetch_checkout_data
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....order import models as order_models
from ...core.enums import TransactionInitializeErrorCode
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error

if TYPE_CHECKING:
    from ....plugins.manager import PluginsManager


class TransactionSessionBase(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_source_object(
        cls,
        info,
        id,
        incorrect_type_error_code: str,
        not_found_error: str,
        manager: "PluginsManager",
    ) -> Union[checkout_models.Checkout, order_models.Order]:
        source_object_type, source_object_id = from_global_id_or_error(
            id, raise_error=False
        )
        if not source_object_type or not source_object_id:
            raise GraphQLError(f"Invalid ID: {id}. Expected one of: Checkout, Order.")

        if source_object_type not in ["Checkout", "Order"]:
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Invalid ID: {id}. Expected one of: Checkout, Order,"
                        + f" received: {source_object_type}.",
                        code=incorrect_type_error_code,
                    )
                }
            )
        source_object: Optional[Union[checkout_models.Checkout, order_models.Order]]
        if source_object_type == "Checkout":
            source_object = (
                checkout_models.Checkout.objects.select_related("channel")
                .prefetch_related("payment_transactions")
                .filter(pk=source_object_id)
                .first()
            )
            if source_object:
                lines, _ = fetch_checkout_lines(source_object)
                checkout_info = fetch_checkout_info(source_object, lines, manager)
                checkout_info, _ = fetch_checkout_data(checkout_info, manager, lines)
                source_object = checkout_info.checkout
        else:
            source_object = (
                order_models.Order.objects.select_related("channel")
                .prefetch_related("payment_transactions")
                .filter(pk=source_object_id)
                .first()
            )

        if not source_object:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "`Order` or `Checkout` not found.",
                        code=not_found_error,
                    )
                }
            )

        if (
            source_object.payment_transactions.count()
            >= settings.TRANSACTION_ITEMS_LIMIT
        ):
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"{source_object_type} transactions limit of "
                        f"{settings.TRANSACTION_ITEMS_LIMIT} reached.",
                        code=TransactionInitializeErrorCode.INVALID.value,
                    )
                }
            )

        return source_object

    @classmethod
    def get_amount(
        cls,
        source_object: Union[checkout_models.Checkout, order_models.Order],
        input_amount: Optional[Decimal],
    ) -> Decimal:
        if input_amount is not None:
            return input_amount
        amount: Decimal = source_object.total_gross_amount
        transactions = source_object.payment_transactions.all()
        for transaction_item in transactions:
            amount_to_reduce = transaction_item.authorized_value
            if amount_to_reduce < transaction_item.charged_value:
                amount_to_reduce = transaction_item.charged_value
            amount -= amount_to_reduce
            amount -= transaction_item.authorize_pending_value
            amount -= transaction_item.charge_pending_value

        return amount if amount >= Decimal(0) else Decimal(0)
