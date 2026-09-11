import graphene

from .mutations import MediaCreate, MediaDelete, MediaReorder, MediaUpdate


class MediaMutations(graphene.ObjectType):
    media_create = MediaCreate.Field()
    media_update = MediaUpdate.Field()
    media_delete = MediaDelete.Field()
    media_reorder = MediaReorder.Field()
