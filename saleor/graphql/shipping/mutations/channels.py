from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ShippingPermissions
from ....shipping.error_codes import ShippingErrorCode
from ....shipping.models import ShippingMethodChannelListing
from ...channel import ChannelContext
from ...channel.types import Channel
from ...channel.utils import (
    validate_duplicated_channel_ids,
    validate_duplicated_channel_values,
)
from ...core.mutations import BaseMutation
from ...core.types.common import ShippingError
from ...utils import resolve_global_ids_to_primary_keys
from ..types import ShippingMethod

if TYPE_CHECKING:
    from ....shipping.models import ShippingMethod as ShippingMethodModel
    from ....channel.models import Channel as ChannelModel

ErrorType = DefaultDict[str, List[ValidationError]]


class ShippingMethodChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID()
    price = graphene.Decimal()
    min_value = graphene.Decimal()
    max_value = graphene.Decimal()


class ShippingMethodChannelListingUpdateInput(graphene.InputObjectType):
    add_channels = graphene.List(
        graphene.NonNull(ShippingMethodChannelListingAddInput),
        description="",
        required=False,
    )
    remove_channels = graphene.List(
        graphene.NonNull(graphene.ID),
        description=(
            "List of channels from which the shipping method should be unassigned."
        ),
        required=False,
    )


class ShippingMethodChannelListingCreate(BaseMutation):
    class Arguments:
        input = ShippingMethodChannelListingAddInput(requred=True, description="")

    class Meta:
        description = "Manage shipping method's availability in channels."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"


class ShippingMethodChannelListingUpdate(BaseMutation):
    shipping_method = graphene.Field(ShippingMethod)

    class Arguments:
        id = graphene.ID()
        input = ShippingMethodChannelListingUpdateInput(requred=True, description="")

    class Meta:
        description = "Manage shipping method's availability in channels."
        permissions = (ShippingPermissions.MANAGE_SHIPPING,)
        error_type_class = ShippingError
        error_type_field = "shipping_errors"

    @classmethod
    def clean_channels(cls, info, input, errors: ErrorType) -> Dict:
        add_channels = input.get("add_channels", [])
        add_channels_ids = [channel["channel_id"] for channel in add_channels]
        remove_channels_ids = input.get("remove_channels", [])
        validate_duplicated_channel_ids(
            add_channels_ids,
            remove_channels_ids,
            errors,
            ShippingErrorCode.DUPLICATED_INPUT_ITEM.value,
        )
        validate_duplicated_channel_values(
            add_channels_ids,
            "add_channels",
            errors,
            ShippingErrorCode.DUPLICATED_INPUT_ITEM.value,
        )
        validate_duplicated_channel_values(
            remove_channels_ids,
            "remove_channels",
            errors,
            ShippingErrorCode.DUPLICATED_INPUT_ITEM.value,
        )

        if errors:
            return {}
        channels_to_add: List["ChannelModel"] = []
        if add_channels_ids:
            channels_to_add = cls.get_nodes_or_error(
                add_channels_ids, "channel_id", Channel
            )
        _, remove_channels_pks = resolve_global_ids_to_primary_keys(
            remove_channels_ids, Channel
        )

        cleaned_input = {"add_channels": [], "remove_channels": remove_channels_pks}

        for channel_listing, channel in zip(add_channels, channels_to_add):
            channel_listing["channel"] = channel
            cleaned_input["add_channels"].append(channel_listing)

        return cleaned_input

    @classmethod
    def add_channels(
        cls, shipping_method: "ShippingMethodModel", add_channels: List[Dict]
    ):
        for add_channel in add_channels:
            defaults = {
                "price": add_channel.get("price"),
                "min_value": add_channel.get("min_value", None),
                "max_value": add_channel.get("max_value", None),
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
    def perform_mutation(cls, _root, info, id, input):
        shipping_method = cls.get_node_or_error(
            info, id, only_type=ShippingMethod, field="id"
        )
        errors = defaultdict(list)

        cleaned_input = cls.clean_channels(info, input, errors)
        if errors:
            raise ValidationError(errors)

        cls.save(info, shipping_method, cleaned_input)
        return ShippingMethodChannelListing(
            product=ChannelContext(node=shipping_method, channel_slug=None)
        )
