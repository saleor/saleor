import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from .....thumbnail import models as thumbnail_models
from ....core.types import CollectionError
from ....plugins.dataloaders import load_plugin_manager
from ...types import Collection
from .collection_create import CollectionCreate, CollectionInput


class CollectionUpdate(CollectionCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to update.")
        input = CollectionInput(
            required=True, description="Fields required to update a collection."
        )

    class Meta:
        description = "Updates a collection."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # delete old background image and related thumbnails
        if "background_image" in cleaned_data and instance.background_image:
            instance.background_image.delete()
            thumbnail_models.Thumbnail.objects.filter(
                collection_id=instance.id
            ).delete()
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        """Override this method with `pass` to avoid triggering product webhook."""
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.collection_updated, instance)
