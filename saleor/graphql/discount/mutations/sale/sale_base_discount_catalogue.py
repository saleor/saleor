from typing import List

from django.core.exceptions import ValidationError

from .....discount.error_codes import DiscountErrorCode
from .....discount.models import PromotionRule
from .....discount.sale_converter import create_catalogue_predicate
from .....product.tasks import (
    update_products_discounted_prices_for_promotion_task,
    update_products_discounted_prices_of_catalogues_task,
)
from .....product.utils import get_products_ids_without_variants
from ....core.mutations import BaseMutation
from ....product.types import Category, Collection, Product, ProductVariant
from ...utils import get_product_ids_for_predicate, merge_migrated_sale_predicates


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
        if products or categories or collections or variants:
            cls.recalculate_discounted_prices(
                products, categories, collections, variants
            )

    @classmethod
    def clean_product(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.value,
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

    @classmethod
    def add_items_to_predicate(
        cls, rules: List[PromotionRule], previous_predicate: dict, input: dict
    ) -> dict:
        if product_ids := input.get("products", []):
            products = cls.get_nodes_or_error(product_ids, "products", Product)
            cls.clean_product(products)
        if category_ids := input.get("categories", []):
            cls.get_nodes_or_error(category_ids, "categories", Category)
        if collection_ids := input.get("collections", []):
            cls.get_nodes_or_error(collection_ids, "collections", Collection)
        if variant_ids := input.get("variants", []):
            cls.get_nodes_or_error(variant_ids, "variants", ProductVariant)

        if product_ids or category_ids or collection_ids or variant_ids:
            predicate_to_merge = create_catalogue_predicate(
                collection_ids, category_ids, product_ids, variant_ids
            )
            new_predicate = merge_migrated_sale_predicates(
                previous_predicate, predicate_to_merge
            )
            for rule in rules:
                rule.catalogue_predicate = new_predicate

            PromotionRule.objects.bulk_update(rules, ["catalogue_predicate"])

            product_ids = get_product_ids_for_predicate(predicate_to_merge)
            update_products_discounted_prices_for_promotion_task.delay(
                list(product_ids)
            )
            return new_predicate
