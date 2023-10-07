import graphene

from .....discount.models import PromotionRule
from .....discount.sale_converter import create_catalogue_predicate_from_catalogue_data
from ...types import Sale
from ..voucher.voucher_add_catalogues import CatalogueInput
from .sale_base_discount_catalogue import BaseDiscountCatalogueMutation


class SaleBaseCatalogueMutation(BaseDiscountCatalogueMutation):
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
    def update_promotion_rules_predicate(cls, rules, catalogue):
        new_predicate = create_catalogue_predicate_from_catalogue_data(catalogue)
        for rule in rules:
            rule.catalogue_predicate = new_predicate
        PromotionRule.objects.bulk_update(rules, ["catalogue_predicate"])
