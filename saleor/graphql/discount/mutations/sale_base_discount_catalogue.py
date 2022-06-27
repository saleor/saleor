from django.core.exceptions import ValidationError

from ....discount.error_codes import DiscountErrorCode
from ....product.tasks import update_products_discounted_prices_of_catalogues_task
from ....product.utils import get_products_ids_without_variants
from ...core.mutations import BaseMutation
from ...product.types import Category, Collection, Product, ProductVariant


class BaseDiscountCatalogueMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def recalculate_discounted_prices(cls, products, categories, collections, variants):
        update_products_discounted_prices_of_catalogues_task.delay(
            product_ids=[p.pk for p in products],
            category_ids=[c.pk for c in categories],
            collection_ids=[c.pk for c in collections],
            variant_ids=[v.pk for v in variants],
        )

    @classmethod
    def add_catalogues_to_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            cls.clean_product(products)
            node.products.add(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.add(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.add(*collections)
        variants = input.get("variants", [])
        if variants:
            variants = cls.get_nodes_or_error(variants, "variants", ProductVariant)
            node.variants.add(*variants)
        # Updated the db entries, recalculating discounts of affected products
        cls.recalculate_discounted_prices(products, categories, collections, variants)

    @classmethod
    def clean_product(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT,
                        params={"products": products_ids_without_variants},
                    )
                }
            )

    @classmethod
    def remove_catalogues_from_node(cls, node, input):
        products = input.get("products", [])
        if products:
            products = cls.get_nodes_or_error(products, "products", Product)
            node.products.remove(*products)
        categories = input.get("categories", [])
        if categories:
            categories = cls.get_nodes_or_error(categories, "categories", Category)
            node.categories.remove(*categories)
        collections = input.get("collections", [])
        if collections:
            collections = cls.get_nodes_or_error(collections, "collections", Collection)
            node.collections.remove(*collections)
        variants = input.get("variants", [])
        if variants:
            variants = cls.get_nodes_or_error(variants, "variants", ProductVariant)
            node.variants.remove(*variants)
        # Updated the db entries, recalculating discounts of affected products
        cls.recalculate_discounted_prices(products, categories, collections, variants)
