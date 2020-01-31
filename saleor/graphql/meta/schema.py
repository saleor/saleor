import graphene

from .mutations import ClearMeta, UpdateMeta


class MetaMutations(graphene.ObjectType):
    clear_meta = ClearMeta.Field()
    update_meta = UpdateMeta.Field()
