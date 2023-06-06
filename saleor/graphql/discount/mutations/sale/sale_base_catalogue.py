import graphene

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
