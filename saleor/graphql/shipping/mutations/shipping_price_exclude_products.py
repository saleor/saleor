import graphene

from ....permission.enums import ShippingPermissions
from ....product import models as product_models
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product import types as product_types
from ..types import ShippingMethodType


class ShippingPriceExcludeProductsInput(BaseInputObjectType):
    products = NonNullList(
        graphene.ID,
        description="List of products which will be excluded.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingPriceExcludeProducts(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethodType,
        description="A shipping method with new list of excluded products.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price.")
        input = ShippingPriceExcludeProductsInput(
            description="Exclude products input.", required=True
        )

    class Meta:
        description = "Exclude products from shipping price."
        doc_category = DOC_CATEGORY_SHIPPING
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        shipping_method = cls.get_node_or_error(
            info, id, qs=models.ShippingMethod.objects
        )
        product_ids = input.get("products", [])

        product_db_ids = cls.get_global_ids_or_error(
            product_ids, product_types.Product, field="products"
        )

        product_to_exclude = product_models.Product.objects.filter(
            id__in=product_db_ids
        )

        current_excluded_products = shipping_method.excluded_products.all()
        shipping_method.excluded_products.set(
            (current_excluded_products | product_to_exclude).distinct()
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_price_updated, shipping_method)

        return ShippingPriceExcludeProducts(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )
