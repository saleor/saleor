import graphene
from graphene_django import DjangoObjectType

from saleor.custom import models
from saleor.graphql.attribute.descriptions import AttributeValueDescriptions


class CategoryCustomType(DjangoObjectType):
    name = graphene.String()
    slug = graphene.String(description=AttributeValueDescriptions.SLUG)

    class Meta:
        description = "Represents an item in the checkout."
        interfaces = [graphene.relay.Node]
        model = models.CategoryCustom
