import graphene
from django.core.exceptions import ValidationError

from .....core.permissions import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductVariant


class ProductVariantSetDefault(BaseMutation):
    product = graphene.Field(Product)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="Id of a product that will have the default variant set.",
        )
        variant_id = graphene.ID(
            required=True,
            description="Id of a variant that will be set as default.",
        )

    class Meta:
        description = (
            "Set default variant for a product. "
            "Mutation triggers PRODUCT_UPDATED webhook."
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, product_id, variant_id
    ):
        qs = models.Product.objects.prefetched_for_webhook()
        product = cls.get_node_or_error(
            info, product_id, field="product_id", only_type=Product, qs=qs
        )
        variant = cls.get_node_or_error(
            info,
            variant_id,
            field="variant_id",
            only_type=ProductVariant,
            qs=models.ProductVariant.objects.select_related("product"),
        )
        if variant.product != product:
            raise ValidationError(
                {
                    "variant_id": ValidationError(
                        "Provided variant doesn't belong to provided product.",
                        code=ProductErrorCode.NOT_PRODUCTS_VARIANT.value,
                    )
                }
            )
        product.default_variant = variant
        product.save(update_fields=["default_variant", "updated_at"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductVariantSetDefault(product=product)
