import graphene
from django.db.models import Exists, OuterRef, Q

from ....attribute import models as models
from ....page import models as page_models
from ....page.utils import mark_pages_search_vector_as_dirty_in_batches
from ....permission.enums import ProductTypePermissions
from ....product import models as product_models
from ....product.utils.search_helpers import (
    mark_products_search_vector_as_dirty_in_batches,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import AttributeError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute, AttributeValue
from .attribute_update import AttributeValueUpdateInput
from .attribute_value_create import AttributeValueCreate


class AttributeValueUpdate(AttributeValueCreate, ModelWithExtRefMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(
            required=False, description="ID of an AttributeValue to update."
        )
        external_reference = graphene.String(
            required=False,
            description="External ID of an AttributeValue to update.",
        )
        input = AttributeValueUpdateInput(
            required=True, description="Fields required to update an AttributeValue."
        )

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = "Updates value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED,
                description="An attribute value was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_UPDATED,
                description="An attribute was updated.",
            ),
        ]

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        if cleaned_input.get("value"):
            cleaned_input["file_url"] = ""
            cleaned_input["content_type"] = ""
        elif cleaned_input.get("file_url"):
            cleaned_input["value"] = ""
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        return super(AttributeValueCreate, cls).perform_mutation(root, info, **data)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = ChannelContext(instance.attribute, None)
        response.attributeValue = ChannelContext(instance, None)
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        cls.mark_search_index_dirty(instance)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_value_updated, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)

    @classmethod
    def mark_search_index_dirty(cls, instance):
        cls._mark_products_search_index_dirty(instance)
        cls._mark_pages_search_index_dirty(instance)

    @classmethod
    def _mark_products_search_index_dirty(cls, instance):
        variants = product_models.ProductVariant.objects.filter(
            Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
        )
        products = product_models.Product.objects.filter(
            Q(search_index_dirty=False)
            & (
                Q(
                    Exists(
                        instance.productvalueassignment.filter(
                            product_id=OuterRef("id")
                        )
                    )
                )
                | Q(Exists(variants.filter(product_id=OuterRef("id"))))
            )
        ).order_by("pk")
        mark_products_search_vector_as_dirty_in_batches(
            list(products.values_list("id", flat=True))
        )

    @classmethod
    def _mark_pages_search_index_dirty(cls, instance):
        pages = page_models.Page.objects.filter(
            Exists(instance.pagevalueassignment.filter(page_id=OuterRef("id")))
        ).order_by("pk")
        mark_pages_search_vector_as_dirty_in_batches(
            list(pages.values_list("id", flat=True))
        )
