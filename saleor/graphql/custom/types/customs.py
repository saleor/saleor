import graphene

from ...core.connection import CountableDjangoObjectType
from ....custom import models


class CustomInput(graphene.InputObjectType):
    title = graphene.String(description="Title ", required=False)
    author = graphene.String(description="Author", required=False)
    yearPublished = graphene.types.datetime.Date(
        description="Year published, format date", required=False)
    review = graphene.Int(description="Review", required=False)


class Custom(CountableDjangoObjectType):
    class Meta:
        model = models.Custom
        interfaces = [graphene.relay.Node]
        only_fields = [
            "id",
            "title",
            "author",
            "yearPublished",
            "review"
        ]
