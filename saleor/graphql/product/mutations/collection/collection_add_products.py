import graphene
from django.core.exceptions import ValidationError

from .....core.permissions import ProductPermissions
from .....core.tracing import traced_atomic_transaction
from .....product import models
from .....product.error_codes import CollectionErrorCode
from .....product.tasks import update_products_discounted_prices_of_catalogues_task
from .....product.utils import get_products_ids_without_variants
from ....channel import ChannelContext
from ....core.mutations import BaseMutation
from ....core.types import CollectionError, NonNullList
from ....plugins.dataloaders import load_plugin_manager
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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(
            products,
            "products",
            Product,
            qs=models.Product.objects.prefetched_for_webhook(single_object=False),
        )
        cls.clean_products(products)
        manager = load_plugin_manager(info.context)
        with traced_atomic_transaction():
            collection.products.add(*products)
            if collection.sale_set.exists():
                # Updated the db entries, recalculating discounts of affected products
                update_products_discounted_prices_of_catalogues_task.delay(
                    product_ids=[pq.pk for pq in products]
                )
            for product in products:
                cls.call_event(manager.product_updated, product)

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
