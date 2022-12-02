from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import ShippingPermissions
from ....core.tracing import traced_atomic_transaction
from ....shipping.error_codes import ShippingErrorCode
from ....shipping.models import ShippingMethodChannelListing
from ....shipping.tasks import (
    drop_invalid_shipping_methods_relations_for_given_channels,
)
from ...channel import ChannelContext
from ...channel.mutations import BaseChannelListingMutation
from ...core.scalars import PositiveDecimal
from ...core.types import NonNullList, ShippingError
from ...core.validators import validate_decimal_max_value, validate_price_precision
from ...shipping.utils import get_shipping_model_by_object_id
from ..types import ShippingMethodType

if TYPE_CHECKING:
    from ....shipping.models import ShippingMethod as ShippingMethodModel

ErrorType = DefaultDict[str, List[ValidationError]]


class ShippingMethodChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    price = PositiveDecimal(
        description="Shipping price of the shipping method in this channel."
    )
    minimum_order_price = PositiveDecimal(
        description="Minimum order price to use this shipping method."
    )
    maximum_order_price = PositiveDecimal(
        description="Maximum order price to use this shipping method."
    )


class ShippingMethodChannelListingInput(graphene.InputObjectType):
    add_channels = NonNullList(
        ShippingMethodChannelListingAddInput,
        description="List of channels to which the shipping method should be assigned.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description=(
            "List of channels from which the shipping method should be unassigned."
        ),
        required=False,
    )


class ShippingMethodChannelListingUpdate(BaseChannelListingMutation):
    shipping_method = graphene.Field(
        ShippingMethodType, description="An updated shipping method instance."
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
            channel = add_channel["channel"]
            defaults = {"currency": channel.currency_code}
            if "minimum_order_price_amount" in add_channel.keys():
                defaults["minimum_order_price_amount"] = add_channel.get(
                    "minimum_order_price_amount", None
                )
            if "maximum_order_price_amount" in add_channel.keys():
                defaults["maximum_order_price_amount"] = add_channel.get(
                    "maximum_order_price_amount", None
                )
            if "price_amount" in add_channel.keys():
                defaults["price_amount"] = add_channel.get("price_amount")
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
        drop_invalid_shipping_methods_relations_for_given_channels.delay(
            [shipping_method.id], remove_channels
        )

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, shipping_method: "ShippingMethodModel", cleaned_input: Dict):
        cls.add_channels(shipping_method, cleaned_input.get("add_channels", []))
        cls.remove_channels(shipping_method, cleaned_input.get("remove_channels", []))

    @classmethod
    def get_shipping_method_channel_listing_to_update(
        cls,
        shipping_method_id,
        input,
    ):
        channels = [data.get("channel") for data in input]
        channel_listings = ShippingMethodChannelListing.objects.filter(
            shipping_method_id=shipping_method_id, channel_id__in=channels
        ).values_list("channel_id", flat=True)
        return [
            data["channel_id"]
            for data in input
            if data["channel"].id in channel_listings
        ]

    @classmethod
    def clean_input(cls, data, shipping_method, errors):
        cleaned_input = data.get("add_channels")
        cls.clean_add_channels(shipping_method, cleaned_input)
        channel_listing_to_update = cls.get_shipping_method_channel_listing_to_update(
            shipping_method.id, cleaned_input
        )
        for channel_input in cleaned_input:
            channel_id = channel_input.get("channel_id")
            price_amount = channel_input.pop("price", None)
            if price_amount is not None:
                try:
                    validate_price_precision(
                        price_amount, channel_input["channel"].currency_code
                    )
                    validate_decimal_max_value(price_amount)
                    channel_input["price_amount"] = price_amount
                except ValidationError as error:
                    error.code = ShippingErrorCode.INVALID.value
                    error.params = {
                        "channels": [channel_id],
                    }
                    errors["price"].append(error)
            else:
                if channel_id not in channel_listing_to_update:
                    errors["price"].append(
                        ValidationError(
                            "This field is required.",
                            code=ShippingErrorCode.REQUIRED,
                            params={"channels": [channel_id]},
                        )
                    )

            min_price = None
            max_price = None
            if "minimum_order_price" in channel_input:
                min_price = channel_input.pop("minimum_order_price")
                channel_input["minimum_order_price_amount"] = min_price
            if min_price is not None:
                try:
                    validate_price_precision(
                        min_price, channel_input["channel"].currency_code
                    )
                    validate_decimal_max_value(min_price)
                except ValidationError as error:
                    error.code = ShippingErrorCode.INVALID.value
                    error.params = {
                        "channels": [channel_id],
                    }
                    errors["minimum_order_price"].append(error)

            if "maximum_order_price" in channel_input:
                max_price = channel_input.pop("maximum_order_price")
                channel_input["maximum_order_price_amount"] = max_price
            if max_price is not None:
                try:
                    validate_price_precision(
                        max_price, channel_input["channel"].currency_code
                    )
                    validate_decimal_max_value(max_price)
                except ValidationError as error:
                    error.code = ShippingErrorCode.INVALID.value
                    error.params = {
                        "channels": [channel_id],
                    }
                    errors["maximum_order_price"].append(error)

            if (
                min_price is not None
                and max_price is not None
                and max_price <= min_price
            ):
                errors["maximum_order_price"].append(
                    ValidationError(
                        (
                            "Maximum order price should be larger than "
                            "the minimum order price."
                        ),
                        code=ShippingErrorCode.MAX_LESS_THAN_MIN,
                        params={"channels": [channel_id]},
                    )
                )

        return data

    @classmethod
    def clean_add_channels(cls, shipping_method, input):
        """Ensure that only channels allowed in the method's shipping zone are added."""
        channels = {data.get("channel").id for data in input}
        available_channels = set(
            shipping_method.shipping_zone.channels.values_list("id", flat=True)
        )
        not_valid_channels = channels - available_channels
        if not_valid_channels:
            channel_ids = [
                graphene.Node.to_global_id("Channel", id) for id in not_valid_channels
            ]
            raise ValidationError(
                {
                    "add_channels": ValidationError(
                        "Cannot add channels that are not assigned "
                        "to the method's shipping zone.",
                        code=ShippingErrorCode.INVALID.value,
                        params={"channels": channel_ids},
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        shipping_method = get_shipping_model_by_object_id(id)

        errors = defaultdict(list)
        clean_channels = cls.clean_channels(
            info, input, errors, ShippingErrorCode.DUPLICATED_INPUT_ITEM.value
        )
        cleaned_input = cls.clean_input(clean_channels, shipping_method, errors)

        if errors:
            raise ValidationError(errors)

        cls.save(info, shipping_method, cleaned_input)
        info.context.plugins.shipping_price_updated(shipping_method)

        return ShippingMethodChannelListingUpdate(
            shipping_method=ChannelContext(node=shipping_method, channel_slug=None)
        )
