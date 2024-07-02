import graphene
from django.db.models import Exists, OuterRef

from ....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.models import ProductChannelListing
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import CollectionError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Collection


class CollectionBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of collection IDs to delete."
        )

    class Meta:
        description = "Deletes collections."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def bulk_action(cls, info, queryset):
        collections_ids = queryset.values_list("id", flat=True)
        collection_products = models.CollectionProduct.objects.filter(
            collection_id__in=collections_ids
        )
        products = list(
            models.Product.objects.filter(
                Exists(collection_products.filter(product_id=OuterRef("id")))
            )
        )
        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.COLLECTION_DELETED)
        for collection in queryset.iterator():
            cls.call_event(manager.collection_deleted, collection, webhooks=webhooks)
        queryset.delete()

        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_UPDATED)
        for product in products:
            cls.call_event(manager.product_updated, product, webhooks=webhooks)

        channel_ids = set(
            ProductChannelListing.objects.filter(
                Exists(collection_products.filter(product_id=OuterRef("product_id")))
            ).values_list("channel_id", flat=True)
        )
        cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)
