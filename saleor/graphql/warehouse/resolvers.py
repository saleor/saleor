from ...warehouse import models


def resolve_stock(id):
    return models.Stock.objects.filter(id=id).first()


def resolve_stocks():
    return models.Stock.objects.all()


def resolve_warehouses():
    return models.Warehouse.objects.all()
