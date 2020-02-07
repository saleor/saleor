import graphene

from .mutations import DeleteMeta, UpdateMeta


class MetaMutations(graphene.ObjectType):
    delete_meta = DeleteMeta.Field()
    update_meta = UpdateMeta.Field()
