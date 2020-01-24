import graphene

from .mutations import UpdateMeta


class MetaMutations(graphene.ObjectType):
    update_meta = UpdateMeta.Field()
