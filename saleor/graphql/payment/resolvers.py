from ...app import models as app_models
from ...order import models as order_models
from ...payment import models
from ..account.utils import get_user_accessible_channels
from ..utils import get_user_or_app_from_context


def resolve_payment_by_id(id):
    return models.Payment.objects.filter(id=id).first()


def resolve_payments(info):
    requestor = get_user_or_app_from_context(info.context)
    payments = models.Payment.objects.all()
    if isinstance(requestor, app_models.App):
        return payments
    accessible_channels = get_user_accessible_channels(requestor)
    orders = order_models.Order.objects.filter(
        channel_id__in=accessible_channels.values("id")
    )
    return payments.filter(order_id__in=orders.values("id"))


def resolve_transaction(id):
    return models.TransactionItem.objects.filter(id=id).first()
