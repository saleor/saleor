import graphene

from ...core.connection import CountableDjangoObjectType
from ....custom import models


class CustomInput(graphene.InputObjectType):
    name = graphene.String(description="Name ", required=False)
    address = graphene.String(description="Address", required=False)


class Custom(CountableDjangoObjectType):
    class Meta:
        model = models.Custom
        interfaces = [graphene.relay.Node]
        only_fields = [
            "id",
            "name",
            "address"
        ]
