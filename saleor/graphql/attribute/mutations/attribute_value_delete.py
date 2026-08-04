from typing import cast

import graphene
from django.db.models import Exists, OuterRef, Q

from ....attribute import models as models
from ....product import models as product_models
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ...core.types import AttributeError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute, AttributeValue
from .permissions import (
    check_any_attribute_type_permission,
    check_attribute_type_permissions,
)


class AttributeValueDelete(ModelDeleteMutation, ModelWithExtRefMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=False, description="ID of a value to delete.")
        external_reference = graphene.String(
            required=False,
            description="External ID of a value to delete.",
        )

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = (
            "Deletes a value of an attribute.\n\nRequires one of the following "
            "permissions, depending on the type of the value's attribute: "
            "MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES for `PRODUCT_TYPE` attributes, "
            "MANAGE_PAGE_TYPES_AND_ATTRIBUTES for `PAGE_TYPE` attributes."
        )
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

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        # Concrete permission is checked after the instance is resolved.
        check_any_attribute_type_permission(cls, info.context)
        instance = cls.get_instance(info, external_reference=external_reference, id=id)
        instance = cast(models.AttributeValue, instance)
        check_attribute_type_permissions(cls, info.context, [instance.attribute.type])
        product_ids = cls.get_product_ids_to_update(instance)
        response = super().perform_mutation(
            _root, info, external_reference=external_reference, id=id
        )
        product_models.Product.objects.filter(id__in=product_ids).update(
            search_index_dirty=True
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_value_deleted, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
        return response

    @classmethod
    def get_product_ids_to_update(cls, instance):
        variants = product_models.ProductVariant.objects.filter(
            Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
        )
        product_ids = product_models.Product.objects.filter(
            Q(Exists(instance.productvalueassignment.filter(product_id=OuterRef("id"))))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = ChannelContext(instance.attribute, None)
        response.attributeValue = ChannelContext(instance, None)
        return response
