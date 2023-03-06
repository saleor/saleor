import graphene

from ....attribute import models as models
from ....core.permissions import ProductTypePermissions
from ...core.mutations import ModelDeleteMutation
from ...core.types import AttributeError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Attribute


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to delete.")

    class Meta:
        model = models.Attribute
        object_type = Attribute
        description = "Deletes an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.attribute_deleted, instance)
