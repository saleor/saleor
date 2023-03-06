import graphene
from django.utils.text import slugify

from ....channel import models
from ....core.permissions import ChannelPermissions
from ....core.tracing import traced_atomic_transaction
from ....tax.models import TaxConfiguration
from ...account.enums import CountryCodeEnum
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31, ADDED_IN_35, ADDED_IN_37, PREVIEW_FEATURE
from ...core.mutations import ModelMutation
from ...core.types import ChannelError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import AllocationStrategyEnum
from ..types import Channel


class StockSettingsInput(graphene.InputObjectType):
    allocation_strategy = AllocationStrategyEnum(
        description=(
            "Allocation strategy options. Strategy defines the preference "
            "of warehouses for allocations and reservations."
        ),
        required=True,
    )


class ChannelInput(graphene.InputObjectType):
    is_active = graphene.Boolean(description="isActive flag.")
    stock_settings = graphene.Field(
        StockSettingsInput,
        description=("The channel stock settings." + ADDED_IN_37 + PREVIEW_FEATURE),
        required=False,
    )
    add_shipping_zones = NonNullList(
        graphene.ID,
        description="List of shipping zones to assign to the channel.",
        required=False,
    )
    add_warehouses = NonNullList(
        graphene.ID,
        description="List of warehouses to assign to the channel."
        + ADDED_IN_35
        + PREVIEW_FEATURE,
        required=False,
    )


class ChannelCreateInput(ChannelInput):
    name = graphene.String(description="Name of the channel.", required=True)
    slug = graphene.String(description="Slug of the channel.", required=True)
    currency_code = graphene.String(
        description="Currency of the channel.", required=True
    )
    default_country = CountryCodeEnum(
        description=(
            "Default country for the channel. Default country can be "
            "used in checkout to determine the stock quantities or calculate taxes "
            "when the country was not explicitly provided."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        ),
        required=True,
    )


class ChannelCreate(ModelMutation):
    class Arguments:
        input = ChannelCreateInput(
            required=True, description="Fields required to create channel."
        )

    class Meta:
        description = "Creates new channel."
        model = models.Channel
        object_type = Channel
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError
        error_type_field = "channel_errors"

    @classmethod
    def get_type_for_model(cls):
        return Channel

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
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
            shipping_zones = cleaned_data.get("add_shipping_zones")
            if shipping_zones:
                instance.shipping_zones.add(*shipping_zones)
            warehouses = cleaned_data.get("add_warehouses")
            if warehouses:
                instance.warehouses.add(*warehouses)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        TaxConfiguration.objects.create(channel=instance)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.channel_created, instance)
