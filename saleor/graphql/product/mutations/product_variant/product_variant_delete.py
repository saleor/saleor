import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.permissions import ProductPermissions
from .....core.tracing import traced_atomic_transaction
from .....order import events as order_events
from .....order import models as order_models
from .....order.tasks import recalculate_orders_task
from .....product import models
from .....product.error_codes import ProductErrorCode
from .....product.search import update_product_search_vector
from .....product.tasks import update_product_discounted_price_task
from ....app.dataloaders import load_app
from ....channel import ChannelContext
from ....core.descriptions import ADDED_IN_38
from ....core.mutations import ModelDeleteMutation
from ....core.types import ProductError
from ....core.validators import validate_one_of_args_is_in_mutation
from ....plugins.dataloaders import load_plugin_manager
from ...types import ProductVariant
from ...utils import get_draft_order_lines_data_for_variants


class ProductVariantDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=False, description="ID of a product variant to delete."
        )
        sku = graphene.String(
            required=False,
            description="SKU of a product variant to delete." + ADDED_IN_38,
        )

    class Meta:
        description = "Deletes a product variant."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        # Update the "discounted_prices" of the parent product
        update_product_discounted_price_task.delay(instance.product_id)
        product = models.Product.objects.get(id=instance.product_id)
        update_product_search_vector(product)
        # if the product default variant has been removed set the new one
        if not product.default_variant:
            product.default_variant = product.variants.first()
            product.save(update_fields=["default_variant", "updated_at"])
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        validate_one_of_args_is_in_mutation(
            ProductErrorCode, "sku", data.get("sku"), "id", data.get("id")
        )
        if node_id := data.get("id"):
            instance = cls.get_node_or_error(info, node_id, only_type=ProductVariant)

        if node_sku := data.get("sku"):
            instance = models.ProductVariant.objects.filter(sku=node_sku).first()
            if not instance:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            f"Couldn't resolve to a node: {node_sku}",
                            code="not_found",
                        )
                    }
                )
            data["id"] = graphene.Node.to_global_id("ProductVariant", instance.id)

        draft_order_lines_data = get_draft_order_lines_data_for_variants([instance.pk])

        # Get cached variant with related fields to fully populate webhook payload.
        variant = (
            models.ProductVariant.objects.prefetch_related(
                "channel_listings", "attributes__values", "variant_media"
            )
        ).get(id=instance.id)
        with traced_atomic_transaction():
            cls.delete_assigned_attribute_values(variant)
            cls.delete_product_channel_listings_without_available_variants(variant)
            response = super().perform_mutation(_root, info, **data)

            # delete order lines for deleted variant
            order_models.OrderLine.objects.filter(
                pk__in=draft_order_lines_data.line_pks
            ).delete()

            # run order event for deleted lines
            app = load_app(info.context)
            for (
                order,
                order_lines,
            ) in draft_order_lines_data.order_to_lines_mapping.items():
                order_events.order_line_variant_removed_event(
                    order, info.context.user, app, order_lines
                )
            manager = load_plugin_manager(info.context)

            order_pks = draft_order_lines_data.order_pks
            if order_pks:
                recalculate_orders_task.delay(list(order_pks))

            cls.call_event(manager.product_variant_deleted, variant)

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        attribute_models.AttributeValue.objects.filter(
            variantassignments__variant_id=instance.id,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()

    @staticmethod
    def delete_product_channel_listings_without_available_variants(instance):
        """Delete invalid product channel listings.

        Delete product channel listings for channels for which the deleted variant
        was the last available variant.
        """
        channel_ids = set(
            instance.channel_listings.values_list("channel_id", flat=True)
        )
        product_id = instance.product_id
        variants = (
            models.ProductVariant.objects.filter(product_id=product_id)
            .exclude(id=instance.id)
            .values("id")
        )
        available_channel_ids = set(
            models.ProductVariantChannelListing.objects.filter(
                Exists(
                    variants.filter(id=OuterRef("variant_id")),
                    channel_id__in=channel_ids,
                )
            ).values_list("channel_id", flat=True)
        )
        not_available_channel_ids = channel_ids - available_channel_ids
        models.ProductChannelListing.objects.filter(
            product_id=product_id, channel_id__in=not_available_channel_ids
        ).delete()
