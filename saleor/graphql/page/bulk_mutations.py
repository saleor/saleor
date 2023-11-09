import graphene
from django.core.exceptions import ValidationError
from django.db.models.expressions import Exists, OuterRef

from ...attribute import AttributeInputType
from ...attribute import models as attribute_models
from ...core.tracing import traced_atomic_transaction
from ...page import models
from ...permission.enums import PagePermissions, PageTypePermissions
from ..core import ResolveInfo
from ..core.mutations import BaseBulkMutation, ModelBulkDeleteMutation
from ..core.types import NonNullList, PageError
from ..plugins.dataloaders import get_plugin_manager_promise
from .types import Page, PageType


class PageBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of page IDs to delete."
        )

    class Meta:
        description = "Deletes pages."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, ids
    ):
        try:
            pks = cls.get_global_ids_or_error(ids, only_type=Page, field="pk")
        except ValidationError as error:
            return 0, error
        cls.delete_assigned_attribute_values(pks)
        return super().perform_mutation(_root, info, ids=ids)

    @staticmethod
    def delete_assigned_attribute_values(instance_pks):
        assigned_values = attribute_models.AssignedPageAttributeValue.objects.filter(
            page_id__in=instance_pks
        )
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )

        attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
        ).delete()


class PageBulkPublish(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of page IDs to (un)publish."
        )
        is_published = graphene.Boolean(
            required=True, description="Determine if pages will be published or not."
        )

    class Meta:
        description = "Publish pages."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def bulk_action(  # type: ignore[override]
        cls, _info: ResolveInfo, queryset, /, is_published
    ):
        queryset.update(is_published=is_published)


class PageTypeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            description="List of page type IDs to delete",
            required=True,
        )

    class Meta:
        description = "Delete page types."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, ids
    ):
        try:
            pks = cls.get_global_ids_or_error(ids, only_type=PageType, field="pk")
        except ValidationError as error:
            return 0, error
        cls.delete_assigned_attribute_values(pks)
        return super().perform_mutation(_root, info, ids=ids)

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        page_types = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        for pt in page_types:
            cls.call_event(manager.page_type_deleted, pt)

    @staticmethod
    def delete_assigned_attribute_values(instance_pks):
        assigned_values = attribute_models.AssignedPageAttributeValue.objects.filter(
            page__page_type_id__in=instance_pks
        )
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )

        attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
        ).delete()
