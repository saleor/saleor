from django.conf import settings

from ...warehouse import models


def resolve_stock(id):
    return (
        models.Stock.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id=id)
        .first()
    )


def resolve_stocks():
    return models.Stock.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).all()


def resolve_warehouses():
    return models.Warehouse.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).all()
