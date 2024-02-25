import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....core.tracing import traced_atomic_transaction
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.inputs import ReorderInput
from ....core.mutations import BaseMutation
from ....core.types import NonNullList, ProductError
from ....core.utils.reordering import perform_reordering
from ....plugins.dataloaders import get_plugin_manager_promise
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
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, moves, product_id
    ):
        pk = cls.get_global_id_or_error(product_id, only_type=Product)

        try:
            product = models.Product.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "product_id": ValidationError(
                        (f"Couldn't resolve to a product type: {product_id}"),
                        code=ProductErrorCode.NOT_FOUND.value,
                    )
                }
            )

        variants_m2m = product.variants.all()
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
                            code=ProductErrorCode.NOT_FOUND.value,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            perform_reordering(variants_m2m, operations)
            product.save(update_fields=["updated_at"])
            cls.call_event(manager.product_updated, product)
            context = ChannelContext(node=product, channel_slug=None)
        return ProductVariantReorder(product=context)
