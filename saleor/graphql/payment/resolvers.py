from ...app import models as app_models
from ...order import models as order_models
from ...payment import models
from ..account.utils import get_user_accessible_channels
from ..core.context import get_database_connection_name
from ..utils import get_user_or_app_from_context


def resolve_payment_by_id(info, id):
    return (
        models.Payment.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )


def resolve_payments(info):
    connection_name = get_database_connection_name(info.context)
    requestor = get_user_or_app_from_context(info.context)
    payments = models.Payment.objects.using(connection_name).all()
    if isinstance(requestor, app_models.App):
        return payments
    accessible_channels = get_user_accessible_channels(info, requestor)
    channel_ids = [channel.id for channel in accessible_channels]
    orders = order_models.Order.objects.using(connection_name).filter(
        channel_id__in=channel_ids
    )
    return payments.filter(order_id__in=orders.values("id"))


def resolve_transaction(info, id):
    if id.isdigit():
        query_params = {"id": id, "use_old_id": True}
    else:
        query_params = {"token": id}
    return (
        models.TransactionItem.objects.using(get_database_connection_name(info.context))
        .filter(**query_params)
        .first()
    )
