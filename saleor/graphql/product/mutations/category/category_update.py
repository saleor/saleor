import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from .....thumbnail import models as thumbnail_models
from ....core.types import ProductError
from ....plugins.dataloaders import load_plugin_manager
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
    def post_save_action(cls, info, instance, _cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.category_updated, instance)
