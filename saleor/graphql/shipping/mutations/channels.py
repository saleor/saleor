from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ShippingPermissions
from ....shipping.error_codes import ShippingErrorCode
from ....shipping.models import ShippingMethodChannelListing
from ...channel import ChannelContext
from ...channel.mutations import BaseChannelListingMutation
from ...core.scalars import Decimal
from ...core.types.common import ShippingError
from ..types import ShippingMethod

if TYPE_CHECKING:
    from ....shipping.models import ShippingMethod as ShippingMethodModel

ErrorType = DefaultDict[str, List[ValidationError]]


class ShippingMethodChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    price = Decimal(
        description="Shipping price of the shipping method in this channel."
    )
    minimum_order_price = Decimal(
        description=("Minimum order price to use this shipping method.")
    )
    maximum_order_price = Decimal(
        description=("Maximum order price to use this shipping method.")
    )


class ShippingMethodChannelListingInput(graphene.InputObjectType):
    add_channels = graphene.List(
        graphene.NonNull(ShippingMethodChannelListingAddInput),
        description="List of channels to which the shipping method should be assigned.",
        required=False,
    )
    remove_channels = graphene.List(
        graphene.NonNull(graphene.ID),
        description=(
            "List of channels from which the shipping method should be unassigned."
        ),
        required=False,
    )


class ShippingMethodChannelListingUpdate(BaseChannelListingMutation):
    shipping_method = graphene.Field(
        ShippingMethod, description="An updated shipping method instance."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a shipping method to update."
        )
        input = ShippingMethodChannelListingInput(
            required=True,
            description="Fields required to update shipping method channel listings.",
        )

    class Meta:
        description = "Manage shipping method's availability in channels."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def add_channels(
        cls, shipping_method: "ShippingMethodModel", add_channels: List[Dict]
    ):
        for add_channel in add_channels:
            defaults = {
                "price_amount": add_channel.get("price_amount"),
                "minimum_order_price_amount": add_channel.get(
                    "minimum_order_price_amount", None
                ),
                "maximum_order_price_amount": add_channel.get(
                    "maximum_order_price_amount", None
                ),
            }
            ShippingMethodChannelListing.objects.update_or_create(
                shipping_method=shipping_method,
                channel=add_channel["channel"],
                defaults=defaults,
            )

    @classmethod
    def remove_channels(
        cls, shipping_method: "ShippingMethodModel", remove_channels: List[int]
    ):
        ShippingMethodChannelListing.objects.filter(
            shipping_method=shipping_method, channel_id__in=remove_channels
        ).delete()

    @classmethod
    @transaction.atomic()
    def save(cls, info, shipping_method: "ShippingMethodModel", cleaned_input: Dict):
        cls.add_channels(shipping_method, cleaned_input.get("add_channels", []))
        cls.remove_channels(shipping_method, cleaned_input.get("remove_channels", []))

    @classmethod
    def clean_input(cls, data):
        cleaned_input = data.get("add_channels")
        for channel_input in cleaned_input:
            price_amount = channel_input.pop("price", None)
            if price_amount is not None:
                if price_amount < 0:
                    raise ValidationError(
                        {
                            "price": ValidationError(
                                ("Shipping rate price cannot be lower than 0."),
                                code=ShippingErrorCode.INVALID,
                            )
                        }
                    )
                channel_input["price_amount"] = price_amount

            min_price = channel_input.pop("minimum_order_price", None)
            max_price = channel_input.pop("maximum_order_price", None)

            if min_price is not None:
                channel_input["minimum_order_price_amount"] = min_price

            if max_price is not None:
                channel_input["maximum_order_price_amount"] = max_price

            if (
                min_price is not None
                and max_price is not None
                and max_price <= min_price
            ):
                raise ValidationError(
                    {
                        "maximum_order_price": ValidationError(
                            (
                                "Maximum order price should be larger than "
                                "the minimum order price."
                            ),
                            code=ShippingErrorCode.MAX_LESS_THAN_MIN,
                        )
                    }
                )
        return data

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        shipping_method = cls.get_node_or_error(
            info, id, only_type=ShippingMethod, field="id"
        )
        errors = defaultdict(list)
        clean_input = cls.clean_input(input)
        clean_channels = cls.clean_channels(
            info, clean_input, errors, ShippingErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        if errors:
            raise ValidationError(errors)

        cls.save(info, shipping_method, clean_channels)
        return ShippingMethodChannelListingUpdate(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )
