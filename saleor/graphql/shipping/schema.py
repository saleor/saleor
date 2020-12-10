import graphene

from ...core.permissions import ShippingPermissions
from ..channel.types import ChannelContext
from ..core.fields import PrefetchingConnectionField
from ..decorators import permission_required
from ..translations.mutations import ShippingPriceTranslate
from .bulk_mutations import ShippingPriceBulkDelete, ShippingZoneBulkDelete
from .mutations.channels import ShippingMethodChannelListingUpdate
from .mutations.shippings import (
    ShippingPriceCreate,
    ShippingPriceDelete,
    ShippingPriceExcludeProducts,
    ShippingPriceRemoveProductFromExclude,
    ShippingPriceUpdate,
    ShippingZipCodeRulesCreate,
    ShippingZipCodeRulesDelete,
    ShippingZoneCreate,
    ShippingZoneDelete,
    ShippingZoneUpdate,
)
from .resolvers import resolve_shipping_zones
from .types import ShippingZone


class ShippingQueries(graphene.ObjectType):
    shipping_zone = graphene.Field(
        ShippingZone,
        id=graphene.Argument(
            graphene.ID, description="ID of the shipping zone.", required=True
        ),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="Look up a shipping zone by ID.",
    )
    shipping_zones = PrefetchingConnectionField(
        ShippingZone,
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of the shop's shipping zones.",
    )

    @permission_required(ShippingPermissions.MANAGE_SHIPPING)
    def resolve_shipping_zone(self, info, id, channel=None):
        instance = graphene.Node.get_node_from_global_id(info, id, ShippingZone)
        return ChannelContext(node=instance, channel_slug=channel) if instance else None

    @permission_required(ShippingPermissions.MANAGE_SHIPPING)
    def resolve_shipping_zones(self, info, channel=None, **_kwargs):
        return resolve_shipping_zones(channel)


class ShippingMutations(graphene.ObjectType):
    shipping_method_channel_listing_update = ShippingMethodChannelListingUpdate.Field()
    shipping_method_zip_code_rules_create = ShippingZipCodeRulesCreate.Field()
    shipping_method_zip_code_rules_delete = ShippingZipCodeRulesDelete.Field()
    shipping_price_create = ShippingPriceCreate.Field()
    shipping_price_delete = ShippingPriceDelete.Field()
    shipping_price_bulk_delete = ShippingPriceBulkDelete.Field()
    shipping_price_update = ShippingPriceUpdate.Field()
    shipping_price_translate = ShippingPriceTranslate.Field()
    shipping_price_exclude_products = ShippingPriceExcludeProducts.Field()
    shipping_price_remove_product_from_exclude = (
        ShippingPriceRemoveProductFromExclude.Field()
    )

    shipping_zone_create = ShippingZoneCreate.Field()
    shipping_zone_delete = ShippingZoneDelete.Field()
    shipping_zone_bulk_delete = ShippingZoneBulkDelete.Field()
    shipping_zone_update = ShippingZoneUpdate.Field()
