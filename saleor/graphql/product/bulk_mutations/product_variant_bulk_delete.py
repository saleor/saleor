from collections.abc import Iterable

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Subquery
from django.db.models.fields import IntegerField
from django.db.models.functions import Coalesce

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.postgres import FlatConcatSearchVector
from ....core.tracing import traced_atomic_transaction
from ....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from ....order import events as order_events
from ....order import models as order_models
from ....order.tasks import recalculate_orders_task
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.search import prepare_product_search_vector_value
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_38
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ProductError
from ...core.validators import validate_one_of_args_is_in_mutation
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ProductVariant
from ..utils import get_draft_order_lines_data_for_variants


class ProductVariantBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=False,
            description="List of product variant IDs to delete.",
        )
        skus = NonNullList(
            graphene.String,
            required=False,
            description="List of product variant SKUs to delete." + ADDED_IN_38,
        )

    class Meta:
        description = "Deletes product variants."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def post_save_actions(cls, info, variants):
        impacted_channels = set()
        for variant in variants:
            channel_ids = [
                listing.channel_id for listing in variant.channel_listings.all()
            ]
            impacted_channels.update(channel_ids)
        # This will finally recalculate discounted prices for products.
        cls.call_event(
            mark_active_catalogue_promotion_rules_as_dirty, impacted_channels
        )

        manager = get_plugin_manager_promise(info.context).get()
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_VARIANT_DELETED)
        for variant in variants:
            cls.call_event(manager.product_variant_deleted, variant, webhooks=webhooks)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info: ResolveInfo, /, ids=None, skus=None, **data):
        validate_one_of_args_is_in_mutation("skus", skus, "ids", ids)

        if ids:
            try:
                pks = cls.get_global_ids_or_error(ids, ProductVariant)
            except ValidationError as error:
                return 0, error
        else:
            pks = models.ProductVariant.objects.filter(sku__in=skus).values_list(
                "pk", flat=True
            )
            ids = [graphene.Node.to_global_id("ProductVariant", pk) for pk in pks]

        draft_order_lines_data = get_draft_order_lines_data_for_variants(pks)

        product_pks = list(
            models.Product.objects.filter(variants__in=pks)
            .distinct()
            .values_list("pk", flat=True)
        )

        # Get cached variants with related fields to fully populate webhook payload.
        variants = list(
            models.ProductVariant.objects.filter(id__in=pks).prefetch_related(
                "channel_listings",
                "attributes__values",
                "variant_media",
            )
        )

        cls.delete_assigned_attribute_values(pks)
        cls.delete_product_channel_listings_without_available_variants(product_pks, pks)
        response = super().perform_mutation(_root, info, ids=ids, **data)

        # delete order lines for deleted variants
        order_models.OrderLine.objects.filter(
            pk__in=draft_order_lines_data.line_pks
        ).delete()

        app = get_app_promise(info.context).get()
        # run order event for deleted lines
        for order, order_lines in draft_order_lines_data.order_to_lines_mapping.items():
            order_events.order_line_variant_removed_event(
                order, info.context.user, app, order_lines
            )

        order_pks = draft_order_lines_data.order_pks
        if order_pks:
            recalculate_orders_task.delay(list(order_pks))

        # set new product default variant if any has been removed
        products = models.Product.objects.filter(
            pk__in=product_pks, default_variant__isnull=True
        )
        for product in products:
            product.search_vector = FlatConcatSearchVector(
                *prepare_product_search_vector_value(product)
            )
            product.default_variant = product.variants.first()
            product.save(
                update_fields=[
                    "default_variant",
                    "search_vector",
                    "updated_at",
                ]
            )

        cls.post_save_actions(info, variants)
        return response

    @staticmethod
    def delete_assigned_attribute_values(instance_pks):
        attribute_models.AttributeValue.objects.filter(
            variantassignments__variant_id__in=instance_pks,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()

    @staticmethod
    def delete_product_channel_listings_without_available_variants(
        product_pks: Iterable[int], variant_pks: Iterable[int]
    ):
        """Delete invalid channel listings.

        Delete product channel listings for product and channel for which
        the last available variant has been deleted.
        """
        variants = models.ProductVariant.objects.filter(
            product_id__in=product_pks
        ).exclude(id__in=variant_pks)

        variant_subquery = Subquery(
            queryset=variants.filter(id=OuterRef("variant_id")).values("product_id"),
            output_field=IntegerField(),
        )
        variant_channel_listings = models.ProductVariantChannelListing.objects.annotate(
            product_id=Coalesce(variant_subquery, 0)
        )

        invalid_product_channel_listings = models.ProductChannelListing.objects.filter(
            product_id__in=product_pks
        ).exclude(
            Exists(
                variant_channel_listings.filter(
                    channel_id=OuterRef("channel_id"), product_id=OuterRef("product_id")
                )
            )
        )
        invalid_product_channel_listings.delete()
