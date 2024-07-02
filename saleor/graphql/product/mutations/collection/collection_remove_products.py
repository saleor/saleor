import graphene

from .....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from .....permission.enums import ProductPermissions
from .....product import models
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import CollectionError, NonNullList
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Collection, Product


class CollectionRemoveProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection from which products will be removed."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = NonNullList(
            graphene.ID, required=True, description="List of product IDs."
        )

    class Meta:
        description = "Remove products from a collection."
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
            only_type=Product,
            qs=models.Product.objects.all(),
        )
        collection.products.remove(*products)
        manager = get_plugin_manager_promise(info.context).get()
        for product in products:
            cls.call_event(manager.product_updated, product)

        if products:
            channel_ids = models.ProductChannelListing.objects.filter(
                product__in=products
            ).values_list("channel_id", flat=True)
            # This will finally recalculate discounted prices for products.
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

        return CollectionRemoveProducts(
            collection=ChannelContext(node=collection, channel_slug=None)
        )
