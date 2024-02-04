import graphene
from django.db.models.expressions import Exists, OuterRef

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.tracing import traced_atomic_transaction
from ....page import models
from ....permission.enums import PagePermissions
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import PageError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Page


class PageDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to delete.")

    class Meta:
        description = "Deletes a page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        page = cls.get_instance(info, **data)
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            cls.delete_assigned_attribute_values(page)
            response = super().perform_mutation(_root, info, **data)
            cls.call_event(manager.page_deleted, page)
        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        assigned_values = attribute_models.AssignedPageAttributeValue.objects.filter(
            page_id=instance.pk
        )
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )

        attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
        ).delete()
