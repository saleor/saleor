import graphene

from .mutations import (
    DeleteMetadata,
    DeletePrivateMetadata,
    UpdateMetadata,
    UpdatePrivateMetadata,
)


class MetaMutations(graphene.ObjectType):
    delete_metadata = DeleteMetadata.Field()
    delete_private_metadata = DeletePrivateMetadata.Field()
    update_metadata = UpdateMetadata.Field()
    update_private_metadata = UpdatePrivateMetadata.Field()
