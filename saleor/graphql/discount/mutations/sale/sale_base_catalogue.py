import graphene

from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion
from ....core import ResolveInfo
from ....core.utils import from_global_id_or_error, raise_validation_error
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
    def get_instance(cls, _info: ResolveInfo, id):
        type, _id = from_global_id_or_error(id, raise_error=False)
        if type == "Promotion":
            raise_validation_error(
                field="id",
                message="Provided ID refers to Promotion model. "
                "Please use 'promotionUpdate' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        object_id = cls.get_global_id_or_error(id, "Sale")
        return Promotion.objects.get(old_sale_id=object_id)
