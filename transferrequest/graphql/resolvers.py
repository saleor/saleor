from transferrequest import models


def resolve_transferrequest(id):
    return models.TransferRequest.objects.filter(id=id).first()


def resolve_transferrequests():
    return models.TransferRequest.objects.all()
