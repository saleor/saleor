import graphene
from django.core.exceptions import ValidationError

from .....core.exceptions import PreorderAllocationError
from .....core.permissions import ProductPermissions
from .....core.tracing import traced_atomic_transaction
from .....product import models
from .....product.error_codes import ProductErrorCode
from .....warehouse.management import deactivate_preorder_for_variant
from ....channel import ChannelContext
from ....core.descriptions import ADDED_IN_31, PREVIEW_FEATURE
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import load_plugin_manager
from ...types import ProductVariant


class ProductVariantPreorderDeactivate(BaseMutation):
    product_variant = graphene.Field(
        ProductVariant, description="Product variant with ended preorder."
    )

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of a variant which preorder should be deactivated.",
        )

    class Meta:
        description = (
            "Deactivates product variant preorder. "
            "It changes all preorder allocation into regular allocation."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError

    @classmethod
    def perform_mutation(cls, _root, info, id):
        qs = models.ProductVariant.objects.prefetched_for_webhook()
        variant = cls.get_node_or_error(
            info, id, field="id", only_type=ProductVariant, qs=qs
        )
        if not variant.is_preorder:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "This variant is not in preorder.",
                        code=ProductErrorCode.INVALID,
                    )
                }
            )
        # transaction ensures triggering event on commit
        with traced_atomic_transaction():
            try:
                deactivate_preorder_for_variant(variant)
            except PreorderAllocationError as error:
                raise ValidationError(
                    str(error),
                    code=ProductErrorCode.PREORDER_VARIANT_CANNOT_BE_DEACTIVATED,
                )
            manager = load_plugin_manager(info.context)
            variant = ChannelContext(node=variant, channel_slug=None)
            cls.call_event(manager.product_variant_updated, variant.node)
        return ProductVariantPreorderDeactivate(product_variant=variant)
