import graphene
from django.db import transaction
from django.db.models import Exists, OuterRef

from ....attribute import AttributeType
from ....attribute import models as models
from ....attribute.lock_objects import attribute_value_qs_select_for_update
from ....core.exceptions import PermissionDenied
from ....page import models as page_models
from ....page.utils import mark_pages_search_vector_as_dirty_in_batches
from ....permission.enums import PageTypePermissions, ProductTypePermissions
from ....product import models as product_models
from ....product.utils.search_helpers import (
    mark_products_search_vector_as_dirty_in_batches,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ...core.types import AttributeError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute


class AttributeDelete(ModelDeleteMutation, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of an attribute to delete.")
        external_reference = graphene.String(
            required=False,
            description="External ID of an attribute to delete.",
        )

    class Meta:
        model = models.Attribute
        object_type = Attribute
        description = (
            "Deletes an attribute.\n\nRequires one of the following permissions, "
            "depending on the attribute type: "
            "MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES for `PRODUCT_TYPE` attributes, "
            "MANAGE_PAGE_TYPES_AND_ATTRIBUTES for `PAGE_TYPE` attributes."
        )
        error_type_class = AttributeError
        error_type_field = "attribute_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_DELETED,
                description="An attribute was deleted.",
            ),
        ]

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = ChannelContext(instance, None)
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_deleted, instance)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        """Perform a mutation that deletes a model instance."""
        # Concrete permission is checked after instance is resolved.
        type_permissions = (
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
            PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
        )
        if not cls.check_permissions(info.context, type_permissions):
            raise PermissionDenied(permissions=type_permissions)

        instance = cls.get_instance(info, external_reference=external_reference, id=id)

        # Check permissions based on attribute type
        permissions: tuple[ProductTypePermissions] | tuple[PageTypePermissions]
        if instance.type == AttributeType.PRODUCT_TYPE:
            permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        else:
            permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied(permissions=permissions)

        product_ids = cls.get_product_ids_to_search_index_update(instance)
        page_ids = cls.get_page_ids_to_search_index_update(instance)

        db_id = instance.id
        with transaction.atomic():
            # Lock the attribute values to prevent concurrent modifications
            locked_qs = attribute_value_qs_select_for_update().filter(
                attribute_id=instance.id
            )
            models.AttributeValue.objects.filter(id__in=locked_qs).delete()
            instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        cls.post_save_action(info, instance, None)
        mark_products_search_vector_as_dirty_in_batches(product_ids)
        mark_pages_search_vector_as_dirty_in_batches(page_ids)
        return cls.success_response(instance)

    @classmethod
    def get_product_ids_to_search_index_update(
        cls, instance: models.Attribute
    ) -> list[int]:
        product_types = product_models.ProductType.objects.filter(
            Exists(instance.attributevariant.filter(product_type_id=OuterRef("id")))
            | Exists(instance.attributeproduct.filter(product_type_id=OuterRef("id")))
        )
        product_ids = product_models.Product.objects.filter(
            Exists(product_types.filter(id=OuterRef("product_type_id")))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def get_page_ids_to_search_index_update(
        cls, instance: models.Attribute
    ) -> list[int]:
        page_types = page_models.PageType.objects.filter(
            Exists(instance.attributepage.filter(page_type_id=OuterRef("id")))
        )
        page_ids = page_models.Page.objects.filter(
            Exists(page_types.filter(id=OuterRef("page_type_id")))
        ).values_list("id", flat=True)
        return list(page_ids)
