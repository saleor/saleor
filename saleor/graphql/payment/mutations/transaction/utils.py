from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address

from .....core.exceptions import PermissionDenied
from .....core.utils import get_client_ip
from .....payment import models as payment_models
from .....payment.error_codes import TransactionUpdateErrorCode
from .....permission.enums import PaymentPermissions
from ....app.dataloaders import get_app_promise
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


def clean_customer_ip_address(
    info, customer_ip_address: Optional[str], error_code: str
):
    """Get customer IP address.

    The customer IP address is required for some payment gateways. By default, the
    customer IP address is taken from the request.

    If customer IP address is provided, we require the app to have the
    `PaymentPermissions.HANDLE_PAYMENTS` permission.
    """

    if not customer_ip_address:
        return get_client_ip(info.context)
    app = get_app_promise(info.context).get()
    if not app or not app.has_perm(PaymentPermissions.HANDLE_PAYMENTS):
        raise PermissionDenied(permissions=[PaymentPermissions.HANDLE_PAYMENTS])
    try:
        validate_ipv46_address(customer_ip_address)
    except ValidationError as error:
        raise ValidationError(
            {
                "customer_ip_address": ValidationError(
                    message=error.message,
                    code=error_code,
                )
            }
        )
    return customer_ip_address
