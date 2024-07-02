import graphene
from django.db.models import Exists, OuterRef

from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....thumbnail import models as thumbnail_models
from ....core import ResolveInfo
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Category
from .category_create import CategoryCreate, CategoryInput


class CategoryUpdate(CategoryCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to update.")
        input = CategoryInput(
            required=True, description="Fields required to update a category."
        )

    class Meta:
        description = "Updates a category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # delete old background image and related thumbnails
        if "background_image" in cleaned_data and instance.background_image:
            instance.background_image.delete()
            thumbnail_models.Thumbnail.objects.filter(category_id=instance.id).delete()
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.category_updated, instance)

        if "metadata" in cleaned_input:
            products = models.Product.objects.filter(category_id=instance.id)
            channel_ids = set(
                models.ProductChannelListing.objects.filter(
                    Exists(products.filter(id=OuterRef("product_id")))
                ).values_list("channel_id", flat=True)
            )
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)
