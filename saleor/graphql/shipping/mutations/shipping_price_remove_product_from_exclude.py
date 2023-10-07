from typing import cast

import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product import types as product_types
from ..types import ShippingMethodType


class ShippingPriceRemoveProductFromExclude(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethodType,
        description="A shipping method with new list of excluded products.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price.")
        products = NonNullList(
            graphene.ID,
            required=True,
            description="List of products which will be removed from excluded list.",
        )

    class Meta:
        description = "Remove product from excluded list for shipping price."
        doc_category = DOC_CATEGORY_SHIPPING
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, products: list
    ):
        shipping_method = cast(
            models.ShippingMethod,
            cls.get_node_or_error(info, id, qs=models.ShippingMethod.objects),
        )

        if products:
            product_db_ids = cls.get_global_ids_or_error(
                products, product_types.Product, field="products"
            )
            shipping_method.excluded_products.set(
                shipping_method.excluded_products.exclude(id__in=product_db_ids)
            )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_price_updated, shipping_method)

        return ShippingPriceRemoveProductFromExclude(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )
