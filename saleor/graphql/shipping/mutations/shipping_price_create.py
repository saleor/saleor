import graphene

from ....permission.enums import ShippingPermissions
from ....shipping import models
from ...channel.types import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_SHIPPING
from ...core.fields import JSONString
from ...core.mutations import ModelMutation
from ...core.scalars import WeightScalar
from ...core.types import BaseInputObjectType, NonNullList, ShippingError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import PostalCodeRuleInclusionTypeEnum, ShippingMethodTypeEnum
from ..types import ShippingMethodType, ShippingZone
from .base import ShippingMethodTypeMixin, ShippingPriceMixin


class ShippingPostalCodeRulesCreateInputRange(BaseInputObjectType):
    start = graphene.String(
        required=True, description="Start range of the postal code."
    )
    end = graphene.String(required=False, description="End range of the postal code.")

    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingPriceInput(BaseInputObjectType):
    name = graphene.String(description="Name of the shipping method.")
    description = JSONString(description="Shipping method description.")
    minimum_order_weight = WeightScalar(
        description="Minimum order weight to use this shipping method."
    )
    maximum_order_weight = WeightScalar(
        description="Maximum order weight to use this shipping method."
    )
    maximum_delivery_days = graphene.Int(
        description="Maximum number of days for delivery."
    )
    minimum_delivery_days = graphene.Int(
        description="Minimal number of days for delivery."
    )
    type = ShippingMethodTypeEnum(description="Shipping type: price or weight based.")
    shipping_zone = graphene.ID(
        description="Shipping zone this method belongs to.", name="shippingZone"
    )
    add_postal_code_rules = NonNullList(
        ShippingPostalCodeRulesCreateInputRange,
        description="Postal code rules to add.",
    )
    delete_postal_code_rules = NonNullList(
        graphene.ID,
        description="Postal code rules to delete.",
    )
    inclusion_type = PostalCodeRuleInclusionTypeEnum(
        description="Inclusion type for currently assigned postal code rules.",
    )
    tax_class = graphene.ID(
        description=(
            "ID of a tax class to assign to this shipping method. If not provided, "
            "the default tax class will be used."
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_SHIPPING


class ShippingPriceCreate(ShippingPriceMixin, ShippingMethodTypeMixin, ModelMutation):
    shipping_zone = graphene.Field(
        ShippingZone,
        description="A shipping zone to which the shipping method belongs.",
    )
    shipping_method = graphene.Field(
        ShippingMethodType, description="A shipping method to create."
    )

    class Arguments:
        input = ShippingPriceInput(
            description="Fields required to create a shipping price.", required=True
        )

    class Meta:
        description = "Creates a new shipping price."
        model = models.ShippingMethod
        object_type = ShippingMethodType
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.shipping_price_created, instance)

    @classmethod
    def success_response(cls, instance):
        shipping_method = ChannelContext(node=instance, channel_slug=None)
        response = super().success_response(shipping_method)
        response.shipping_zone = ChannelContext(
            node=instance.shipping_zone, channel_slug=None
        )
        return response
