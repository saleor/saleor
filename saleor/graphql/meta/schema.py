import graphene

from .mutations import DeleteMeta, UpdateMeta, UpdatePrivateMeta


class MetaMutations(graphene.ObjectType):
    delete_meta = DeleteMeta.Field()
    update_meta = UpdateMeta.Field()
    update_private_meta = UpdatePrivateMeta.Field()
