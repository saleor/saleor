import graphene
from .mutations import AlterProductMutations


class AlternativeProductMutations(graphene.ObjectType):
    alter_product = AlterProductMutations.Field()
