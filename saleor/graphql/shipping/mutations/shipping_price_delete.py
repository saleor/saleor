from typing import cast

import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.mutations import BaseMutation
from ...core.types import ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import ShippingMethodType, ShippingZone


class ShippingPriceDelete(BaseMutation):
    shipping_method = graphene.Field(
        ShippingMethodType, description="A shipping method to delete."
    )
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a shipping price to delete.")

    class Meta:
        description = "Deletes a shipping price."
        doc_category = DOC_CATEGORY_SHIPPING
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        shipping_method = cast(
            models.ShippingMethod,
            cls.get_node_or_error(info, id, qs=models.ShippingMethod.objects),
        )
        shipping_method_id = shipping_method.id
        shipping_zone = shipping_method.shipping_zone
        shipping_method.delete()
        shipping_method.id = shipping_method_id
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_price_deleted, shipping_method)

        return ShippingPriceDelete(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None),
            shipping_zone=ChannelContext(node=shipping_zone, channel_slug=None),
        )
