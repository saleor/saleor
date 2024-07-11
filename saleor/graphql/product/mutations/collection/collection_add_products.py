import graphene
from django.core.exceptions import ValidationError

from .....core.tracing import traced_atomic_transaction
from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import CollectionErrorCode
from .....product.utils import get_products_ids_without_variants
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import CollectionError, NonNullList
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Collection, Product


class CollectionAddProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection to which products will be added."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = NonNullList(
            graphene.ID, required=True, description="List of product IDs."
        )

    class Meta:
        description = "Adds products to a collection."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, collection_id, products
    ):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(
            products,
            "products",
            Product,
            qs=models.Product.objects.all(),
        )
        cls.clean_products(products)
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            collection.products.add(*products)
            for product in products:
                cls.call_event(manager.product_updated, product)

        if products:
            channel_ids = models.ProductChannelListing.objects.filter(
                product_id__in=[product.id for product in products]
            ).values_list("channel_id", flat=True)
            # This will finally recalculate discounted prices for products.
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

        return CollectionAddProducts(
            collection=ChannelContext(node=collection, channel_slug=None)
        )

    @classmethod
    def clean_products(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            code = CollectionErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.value
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=code,
                        params={"products": products_ids_without_variants},
                    )
                }
            )
