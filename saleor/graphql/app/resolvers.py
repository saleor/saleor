import graphene_django_optimizer as gql_optimizer

from ...app import models


def resolve_apps(info, **_kwargs):
    qs = models.App.objects.all()
    return gql_optimizer.query(qs, info)
