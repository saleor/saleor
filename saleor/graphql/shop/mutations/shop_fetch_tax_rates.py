import graphene

from ....permission.enums import SitePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHOP
from ...core.mutations import BaseMutation
from ...core.types import ShopError
from ..types import Shop


class ShopFetchTaxRates(BaseMutation):
    shop = graphene.Field(Shop, description="Updated shop.")

    class Meta:
        description = "Fetch tax rates."
        doc_category = DOC_CATEGORY_SHOP
        permissions = (SitePermissions.MANAGE_SETTINGS,)
        error_type_class = ShopError
        error_type_field = "shop_errors"

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /):
        # This mutation is deprecated and will be removed in Saleor 4.0.
        return ShopFetchTaxRates(shop=Shop())
