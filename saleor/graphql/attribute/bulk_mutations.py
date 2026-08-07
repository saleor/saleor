import graphene
from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q

from ...attribute import models
from ...attribute.lock_objects import attribute_value_qs_select_for_update
from ...product import models as product_models
from ...product.utils.search_helpers import (
    mark_products_search_vector_as_dirty_in_batches,
)
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.utils import get_webhooks_for_event
from ..core import ResolveInfo
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types import AttributeError, NonNullList
from ..core.utils import WebhookEventInfo
from ..plugins.dataloaders import get_plugin_manager_promise
from ..utils import resolve_global_ids_to_primary_keys
from .mutations.permissions import (
    check_any_attribute_type_permission,
    check_attribute_type_permissions,
)
from .types import Attribute, AttributeValue


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                f"List of attribute IDs to delete. The number of items is limited to {settings.BULK_DELETE_LIMIT} by default. "
                "Exceeding the limit returns an `INVALID` error."
            ),
        )

    class Meta:
        description = (
            "Deletes attributes.\n\nRequires one of the following permissions, "
            "depending on the type of each attribute: "
            "MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES for `PRODUCT_TYPE` attributes, "
            "MANAGE_PAGE_TYPES_AND_ATTRIBUTES for `PAGE_TYPE` attributes, "
            "MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES for `CUSTOMER_TYPE` attributes."
        )
        model = models.Attribute
        object_type = Attribute
        error_type_class = AttributeError
        error_type_field = "attribute_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_DELETED,
                description="An attribute was deleted.",
            ),
        ]
        max_input_size = settings.BULK_DELETE_LIMIT

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, ids
    ):
        # Concrete permissions are checked after attribute types are resolved.
        check_any_attribute_type_permission(cls, info.context)
        if not ids:
            return 0, {}
        if size_error := cls.validate_input_size(ids):
            return 0, size_error
        _, attribute_pks = resolve_global_ids_to_primary_keys(ids, "Attribute")
        attribute_types = (
            models.Attribute.objects.filter(pk__in=attribute_pks)
            .values_list("type", flat=True)
            .distinct()
        )
        check_attribute_type_permissions(cls, info.context, attribute_types)
        product_ids = cls.get_product_ids_to_update(attribute_pks)
        response = super().perform_mutation(root, info, ids=ids)
        mark_products_search_vector_as_dirty_in_batches(product_ids)
        return response

    @classmethod
    def get_product_ids_to_update(cls, attribute_pks):
        attribute_variant = models.AttributeVariant.objects.filter(
            attribute_id__in=attribute_pks
        )
        assigned_variant_attrs = models.AssignedVariantAttribute.objects.filter(
            Exists(attribute_variant.filter(id=OuterRef("assignment_id")))
        )
        variants = product_models.ProductVariant.objects.filter(
            Exists(assigned_variant_attrs.filter(variant_id=OuterRef("id")))
        )

        attribute_product = models.AttributeProduct.objects.filter(
            attribute_id__in=attribute_pks
        )

        product_ids = product_models.Product.objects.filter(
            Exists(
                attribute_product.filter(product_type_id=OuterRef("product_type_id"))
            )
            | Exists(variants.filter(product_id=OuterRef("id")))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        attributes = list(queryset)
        queryset.delete()
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.ATTRIBUTE_DELETED)
        for attribute in attributes:
            cls.call_event(manager.attribute_deleted, attribute, webhooks=webhooks)


class AttributeValueBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                "List of attribute value IDs to delete. The number of items is "
                f"limited to {settings.BULK_DELETE_LIMIT} by default. Exceeding the limit returns an `INVALID` error."
            ),
        )

    class Meta:
        description = (
            "Deletes values of attributes.\n\nRequires one of the following "
            "permissions, depending on the type of each value's attribute: "
            "MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES for `PRODUCT_TYPE` attributes, "
            "MANAGE_PAGE_TYPES_AND_ATTRIBUTES for `PAGE_TYPE` attributes, "
            "MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES for `CUSTOMER_TYPE` attributes."
        )
        model = models.AttributeValue
        object_type = AttributeValue
        error_type_class = AttributeError
        error_type_field = "attribute_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED,
                description="An attribute value was deleted.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_UPDATED,
                description="An attribute was updated.",
            ),
        ]
        max_input_size = settings.BULK_DELETE_LIMIT

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, ids
    ):
        # Concrete permissions are checked after attribute types are resolved.
        check_any_attribute_type_permission(cls, info.context)
        if not ids:
            return 0, {}
        if size_error := cls.validate_input_size(ids):
            return 0, size_error
        _, value_pks = resolve_global_ids_to_primary_keys(ids, "AttributeValue")
        attribute_types = (
            models.AttributeValue.objects.filter(pk__in=value_pks)
            .values_list("attribute__type", flat=True)
            .distinct()
        )
        check_attribute_type_permissions(cls, info.context, attribute_types)
        product_ids = cls.get_product_ids_to_update(value_pks)
        response = super().perform_mutation(root, info, ids=ids)
        mark_products_search_vector_as_dirty_in_batches(product_ids)
        return response

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /):
        attributes = {value.attribute for value in queryset}
        with transaction.atomic():
            locked_qs = attribute_value_qs_select_for_update()
            locked_qs = locked_qs.filter(pk__in=queryset.values_list("pk", flat=True))
            values = list(locked_qs)
            queryset.delete()

        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.ATTRIBUTE_VALUE_DELETED)
        for value in values:
            cls.call_event(manager.attribute_value_deleted, value, webhooks=webhooks)
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.ATTRIBUTE_UPDATED)
        for attribute in attributes:
            cls.call_event(manager.attribute_updated, attribute, webhooks=webhooks)

    @classmethod
    def get_product_ids_to_update(cls, value_pks):
        assigned_product_values = models.AssignedProductAttributeValue.objects.filter(
            value_id__in=value_pks
        )

        assigned_variant_values = models.AssignedVariantAttributeValue.objects.filter(
            value_id__in=value_pks
        )
        assigned_variant_attrs = models.AssignedVariantAttribute.objects.filter(
            Exists(assigned_variant_values.filter(assignment_id=OuterRef("id")))
        )
        variants = product_models.ProductVariant.objects.filter(
            Exists(assigned_variant_attrs.filter(variant_id=OuterRef("id")))
        )

        product_ids = product_models.Product.objects.filter(
            Exists(assigned_product_values.filter(product_id=OuterRef("id")))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)
