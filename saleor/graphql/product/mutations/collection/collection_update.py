import graphene
from django.db.models import Exists, OuterRef

from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....thumbnail import models as thumbnail_models
from ....core import ResolveInfo
from ....core.types import CollectionError
from ....plugins.dataloaders import get_plugin_manager_promise
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
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        """Override this method with `pass` to avoid triggering product webhook."""
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.collection_updated, instance)

        if "metadata" in cleaned_input:
            collection_products = models.CollectionProduct.objects.filter(
                collection_id=instance.id
            )
            channel_ids = set(
                models.ProductChannelListing.objects.filter(
                    Exists(
                        collection_products.filter(product_id=OuterRef("product_id"))
                    )
                ).values_list("channel_id", flat=True)
            )
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)
