import graphene_django_optimizer as gql_optimizer

from ...shipping import models


def resolve_shipping_zones(info):
    qs = models.ShippingZone.objects.all()
    return gql_optimizer.query(qs, info)
