import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....core.permissions import ProductPermissions
from .....core.tracing import traced_atomic_transaction
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core.inputs import ReorderInput
from ....core.mutations import BaseMutation
from ....core.types import NonNullList, ProductError
from ....core.utils.reordering import perform_reordering
from ....plugins.dataloaders import load_plugin_manager
from ...types import Product, ProductVariant


class ProductVariantReorder(BaseMutation):
    product = graphene.Field(Product)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="Id of product that variants order will be altered.",
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of variant reordering operations.",
        )

    class Meta:
        description = (
            "Reorder the variants of a product. "
            "Mutation updates updated_at on product and "
            "triggers PRODUCT_UPDATED webhook."
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id, moves):
        pk = cls.get_global_id_or_error(product_id, only_type=Product)

        try:
            product = models.Product.objects.prefetched_for_webhook().get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "product_id": ValidationError(
                        (f"Couldn't resolve to a product type: {product_id}"),
                        code=ProductErrorCode.NOT_FOUND,
                    )
                }
            )

        variants_m2m = product.variants
        operations = {}

        for move_info in moves:
            variant_pk = cls.get_global_id_or_error(
                move_info.id, only_type=ProductVariant, field="moves"
            )

            try:
                m2m_info = variants_m2m.get(id=int(variant_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to a variant: {move_info.id}",
                            code=ProductErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order
        manager = load_plugin_manager(info.context)
        with traced_atomic_transaction():
            perform_reordering(variants_m2m, operations)
            product.save(update_fields=["updated_at"])
            cls.call_event(manager.product_updated, product)
            product = ChannelContext(node=product, channel_slug=None)
        return ProductVariantReorder(product=product)
