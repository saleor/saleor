from custom import models


def resolve_custom(id):
    return models.Custom.objects.filter(id=id).first()


def resolve_stocks():
    return models.Custom.objects.all()
