import graphene

from .mutations import DeleteMeta, DeletePrivateMeta, UpdateMeta, UpdatePrivateMeta


class MetaMutations(graphene.ObjectType):
    delete_meta = DeleteMeta.Field()
    delete_private_meta = DeletePrivateMeta.Field()
    update_meta = UpdateMeta.Field()
    update_private_meta = UpdatePrivateMeta.Field()
