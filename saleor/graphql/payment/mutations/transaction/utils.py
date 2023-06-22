from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError

from .....payment import models as payment_models
from .....payment.error_codes import TransactionUpdateErrorCode
from ....core.utils import from_global_id_or_error
from ...types import TransactionItem

if TYPE_CHECKING:
    pass


def get_transaction_item(id: str) -> payment_models.TransactionItem:
    """Get transaction based on global ID.

    The transactions created before 3.13 were using the `id` field as a graphql ID.
    From 3.13, the `token` is used as a graphql ID. All transactionItems created
    before 3.13 will use an `int` id as an identification.
    """
    _, db_id = from_global_id_or_error(
        global_id=id, only_type=TransactionItem, raise_error=True
    )
    if db_id.isdigit():
        query_params = {"id": db_id, "use_old_id": True}
    else:
        query_params = {"token": db_id}
    instance = payment_models.TransactionItem.objects.filter(**query_params).first()
    if not instance:
        raise ValidationError(
            {
                "id": ValidationError(
                    f"Couldn't resolve to a node: {id}",
                    code=TransactionUpdateErrorCode.NOT_FOUND.value,
                )
            }
        )
    return instance
