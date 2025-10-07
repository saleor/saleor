from typing import cast

import graphene

from ....attribute import models as models
from ....page.utils import mark_pages_search_vector_as_dirty_in_batches
from ....permission.enums import ProductTypePermissions
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
from ..types import Attribute, AttributeValue
from .utils import (
    get_page_ids_to_search_index_update_for_attribute_values,
    get_product_ids_to_search_index_update_for_attribute_values,
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
        description = "Deletes a value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
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
        instance = cls.get_instance(info, external_reference=external_reference, id=id)
        instance = cast(models.AttributeValue, instance)
        product_ids = get_product_ids_to_search_index_update_for_attribute_values(
            [instance]
        )
        page_ids = get_page_ids_to_search_index_update_for_attribute_values([instance])
        response = super().perform_mutation(
            _root, info, external_reference=external_reference, id=id
        )
        mark_products_search_vector_as_dirty_in_batches(product_ids)
        mark_pages_search_vector_as_dirty_in_batches(page_ids)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_value_deleted, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
        return response

    @classmethod
    def success_response(cls, instance: models.AttributeValue):
        response = super().success_response(instance)
        response.attribute = ChannelContext(instance.attribute, None)
        response.attributeValue = ChannelContext(instance, None)
        return response
