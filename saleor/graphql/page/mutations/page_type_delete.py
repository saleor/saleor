import graphene
from django.db.models.expressions import Exists, OuterRef

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.tracing import traced_atomic_transaction
from ....page import models
from ....permission.enums import PageTypePermissions
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import PageError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import PageType


class PageTypeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of the page type to delete.")

    class Meta:
        description = "Delete a page type."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        page_type_pk = cls.get_global_id_or_error(id, only_type=PageType, field="pk")
        with traced_atomic_transaction():
            cls.delete_assigned_attribute_values(page_type_pk)
            return super().perform_mutation(_root, info, id=id)

    @staticmethod
    def delete_assigned_attribute_values(instance_pk):
        assigned_values = attribute_models.AssignedPageAttributeValue.objects.filter(
            page__page_type_id=instance_pk
        )
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )

        attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
        ).delete()

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_type_deleted, instance)
