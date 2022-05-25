import graphene

from ...tax import models
from ..channel.dataloaders import ChannelByIdLoader
from ..channel.types import Channel
from ..core.connection import CountableConnection
from ..core.descriptions import ADDED_IN_35, PREVIEW_FEATURE
from ..core.types import ModelObjectType


class TaxConfiguration(ModelObjectType):
    channel = graphene.Field(
        Channel,
        description="A channel to which the tax configuration applies to.",
        required=True,
    )
    charge_taxes = graphene.Boolean(
        description="Determines whether taxes are charged in the given channel.",
        required=True,
    )
    display_gross_prices = graphene.Boolean(description="", required=True)
    prices_entered_with_tax = graphene.Boolean(description="", required=True)

    class Meta:
        description = (
            "Channel-specific tax configuration." + ADDED_IN_35 + PREVIEW_FEATURE
        )
        interfaces = [graphene.relay.Node]
        model = models.TaxConfiguration

    @staticmethod
    def resolve_channel(root, info):
        return ChannelByIdLoader(info.context).load(root.channel_id)


class TaxConfigurationCountableConnection(CountableConnection):
    class Meta:
        node = TaxConfiguration
