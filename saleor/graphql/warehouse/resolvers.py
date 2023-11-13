from ...warehouse import models
from ..core.context import get_database_connection_name


def resolve_stock(info, id):
    return (
        models.Stock.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )


def resolve_stocks(info):
    return models.Stock.objects.using(get_database_connection_name(info.context)).all()


def resolve_warehouses(info):
    return models.Warehouse.objects.using(
        get_database_connection_name(info.context)
    ).all()
