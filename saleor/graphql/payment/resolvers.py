from ...payment import models


def resolve_payment_by_id(id):
    return models.Payment.objects.filter(id=id).first()


def resolve_payments(info):
    return models.Payment.objects.all()


def resolve_transaction(id):
    return models.TransactionItem.objects.filter(id=id).first()
