import graphene_django_optimizer as gql_optimizer

from ....app.models import App


def resolve_service_accounts(info, **_kwargs):
    qs = App.objects.all()
    return gql_optimizer.query(qs, info)
