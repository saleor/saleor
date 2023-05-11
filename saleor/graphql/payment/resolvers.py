from ...payment import models


def resolve_payment_by_id(id):
    return models.Payment.objects.filter(id=id).first()


def resolve_payments(info):
    return models.Payment.objects.all()


def resolve_transaction(id):
    if id.isdigit():
        query_params = {"id": id, "use_old_id": True}
    else:
        query_params = {"token": id}
    return models.TransactionItem.objects.filter(**query_params).first()
