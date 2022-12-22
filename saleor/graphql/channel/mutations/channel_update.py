import graphene
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from ....channel import models
from ....channel.error_codes import ChannelErrorCode
from ....core.permissions import ChannelPermissions
from ....core.tracing import traced_atomic_transaction
from ....shipping.tasks import (
    drop_invalid_shipping_methods_relations_for_given_channels,
)
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31, ADDED_IN_35, PREVIEW_FEATURE
from ...core.mutations import ModelMutation
from ...core.types import ChannelError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..types import Channel
from ..utils import delete_invalid_warehouse_to_shipping_zone_relations
from .channel_create import ChannelInput


class ChannelUpdateInput(ChannelInput):
    name = graphene.String(description="Name of the channel.")
    slug = graphene.String(description="Slug of the channel.")
    default_country = CountryCodeEnum(
        description=(
            "Default country for the channel. Default country can be "
            "used in checkout to determine the stock quantities or calculate taxes "
            "when the country was not explicitly provided." + ADDED_IN_31
        )
    )
    remove_shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zones to unassign from the channel.",
        required=False,
    )
    remove_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to unassign from the channel."
        + ADDED_IN_35
        + PREVIEW_FEATURE,
        required=False,
    )


class ChannelUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a channel to update.")
        input = ChannelUpdateInput(
            description="Fields required to update a channel.", required=True
        )

    class Meta:
        description = "Update a channel."
        model = models.Channel
        object_type = Channel
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        errors = {}
        if error := check_for_duplicates(
            data, "add_shipping_zones", "remove_shipping_zones", "shipping_zones"
        ):
            error.code = ChannelErrorCode.DUPLICATED_INPUT_ITEM.value
            errors["shipping_zones"] = error

        if error := check_for_duplicates(
            data, "add_warehouses", "remove_warehouses", "warehouses"
        ):
            error.code = ChannelErrorCode.DUPLICATED_INPUT_ITEM.value
            errors["warehouses"] = error

        if errors:
            raise ValidationError(errors)

        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        slug = cleaned_input.get("slug")
        if slug:
            cleaned_input["slug"] = slugify(slug)
        if stock_settings := cleaned_input.get("stock_settings"):
            cleaned_input["allocation_strategy"] = stock_settings["allocation_strategy"]

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        with traced_atomic_transaction():
            super()._save_m2m(info, instance, cleaned_data)
            cls._update_shipping_zones(instance, cleaned_data)
            cls._update_warehouses(instance, cleaned_data)
            if (
                "remove_shipping_zones" in cleaned_data
                or "remove_warehouses" in cleaned_data
            ):
                warehouse_ids = [
                    warehouse.id
                    for warehouse in cleaned_data.get("remove_warehouses", [])
                ]
                shipping_zone_ids = [
                    warehouse.id
                    for warehouse in cleaned_data.get("remove_shipping_zones", [])
                ]
                delete_invalid_warehouse_to_shipping_zone_relations(
                    instance, warehouse_ids, shipping_zone_ids
                )

    @classmethod
    def _update_shipping_zones(cls, instance, cleaned_data):
        add_shipping_zones = cleaned_data.get("add_shipping_zones")
        if add_shipping_zones:
            instance.shipping_zones.add(*add_shipping_zones)
        remove_shipping_zones = cleaned_data.get("remove_shipping_zones")
        if remove_shipping_zones:
            instance.shipping_zones.remove(*remove_shipping_zones)
            shipping_channel_listings = instance.shipping_method_listings.filter(
                shipping_method__shipping_zone__in=remove_shipping_zones
            )
            shipping_method_ids = list(
                shipping_channel_listings.values_list("shipping_method_id", flat=True)
            )
            shipping_channel_listings.delete()
            drop_invalid_shipping_methods_relations_for_given_channels.delay(
                shipping_method_ids, [instance.id]
            )

    @classmethod
    def _update_warehouses(cls, instance, cleaned_data):
        add_warehouses = cleaned_data.get("add_warehouses")
        if add_warehouses:
            instance.warehouses.add(*add_warehouses)
        remove_warehouses = cleaned_data.get("remove_warehouses")
        if remove_warehouses:
            instance.warehouses.remove(*remove_warehouses)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.channel_updated, instance)
