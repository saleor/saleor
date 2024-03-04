from collections import defaultdict
from typing import Union

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef

from .....discount.error_codes import DiscountErrorCode
from .....product import models as product_models
from .....product.utils import get_products_ids_without_variants
from .....product.utils.product import mark_products_in_channels_as_dirty
from ....core import ResolveInfo
from ....core.mutations import BaseMutation
from ....plugins.dataloaders import get_plugin_manager_promise
from ....product.types import Category, Collection, Product, ProductVariant
from ...types import Sale
from ...utils import (
    convert_catalogue_info_into_predicate,
    get_variants_for_catalogue_predicate,
)
from ..utils import update_variants_for_promotion
from ..voucher.voucher_add_catalogues import CatalogueInput

CatalogueInfo = defaultdict[str, set[Union[int, str]]]


class SaleBaseCatalogueMutation(BaseMutation):
    sale = graphene.Field(
        Sale, description="Sale of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale.")
        input = CatalogueInput(
            required=True,
            description="Fields required to modify catalogue IDs of sale.",
        )

    class Meta:
        abstract = True

    @classmethod
    def post_save_actions(
        cls, info: ResolveInfo, promotion, previous_catalogue, new_catalogue
    ):
        if previous_catalogue != new_catalogue:
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(
                manager.sale_updated,
                promotion,
                previous_catalogue,
                new_catalogue,
            )

        previous_predicate = convert_catalogue_info_into_predicate(previous_catalogue)
        new_predicate = convert_catalogue_info_into_predicate(new_catalogue)
        previous_product_ids = cls.get_product_ids_for_predicate(previous_predicate)
        new_variants = get_variants_for_catalogue_predicate(new_predicate)
        new_product_ids = set(
            product_models.Product.objects.filter(
                Exists(new_variants.filter(product_id=OuterRef("id")))
            ).values_list("id", flat=True)
        )
        update_variants_for_promotion(new_variants, promotion)

        if previous_product_ids != new_product_ids:
            is_add_mutation = len(new_product_ids) > len(previous_product_ids)
            if is_add_mutation:
                product_ids = new_product_ids - previous_product_ids
            else:
                product_ids = previous_product_ids - new_product_ids

            rules = promotion.rules.all()
            PromotionRuleChannel = rules.model.channels.through
            channel_ids = PromotionRuleChannel.objects.filter(
                Exists(rules.filter(id=OuterRef("promotionrule_id")))
            ).values_list("channel_id", flat=True)
            cls.call_event(
                mark_products_in_channels_as_dirty,
                {channel_id: product_ids for channel_id in channel_ids},
            )

    @classmethod
    def get_product_ids_for_predicate(cls, predicate: dict) -> set[int]:
        variants = get_variants_for_catalogue_predicate(predicate)
        products = product_models.Product.objects.filter(
            Exists(variants.filter(product_id=OuterRef("id")))
        )
        return set(products.values_list("id", flat=True))

    @classmethod
    def get_catalogue_info_from_input(cls, input) -> CatalogueInfo:
        catalogue_info: CatalogueInfo = defaultdict(set)
        if collection_ids := input.get("collections", set()):
            cls.get_nodes_or_error(collection_ids, "collections", Collection)
        if category_ids := input.get("categories", set()):
            cls.get_nodes_or_error(category_ids, "categories", Category)
        if product_ids := input.get("products", set()):
            products = cls.get_nodes_or_error(product_ids, "products", Product)
            cls.clean_product(products)
        if variant_ids := input.get("variants", set()):
            cls.get_nodes_or_error(variant_ids, "variants", ProductVariant)

        catalogue_info["collections"] = set(collection_ids)
        catalogue_info["categories"] = set(category_ids)
        catalogue_info["products"] = set(product_ids)
        catalogue_info["variants"] = set(variant_ids)

        return catalogue_info

    @classmethod
    def clean_product(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            error_code = DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.value
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=error_code,
                        params={"products": products_ids_without_variants},
                    )
                }
            )
