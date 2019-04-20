import graphene
from graphql_jwt.decorators import permission_required

from ..core.fields import PrefetchingConnectionField
from ..translations.mutations import ShippingPriceTranslate
from .bulk_mutations import ShippingPriceBulkDelete, ShippingZoneBulkDelete
from .mutations import (
    ShippingPriceCreate, ShippingPriceDelete, ShippingPriceUpdate,
    ShippingZoneCreate, ShippingZoneDelete, ShippingZoneUpdate)
from .resolvers import resolve_shipping_zones
from .types import ShippingZone


class ShippingQueries(graphene.ObjectType):
    shipping_zone = graphene.Field(
        ShippingZone, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a shipping zone by ID.')
    shipping_zones = PrefetchingConnectionField(
        ShippingZone, description='List of the shop\'s shipping zones.')

    @permission_required('shipping.manage_shipping')
    def resolve_shipping_zone(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ShippingZone)

    @permission_required('shipping.manage_shipping')
    def resolve_shipping_zones(self, info, **_kwargs):
        return resolve_shipping_zones(info)


class ShippingMutations(graphene.ObjectType):
    shipping_price_create = ShippingPriceCreate.Field()
    shipping_price_delete = ShippingPriceDelete.Field()
    shipping_price_bulk_delete = ShippingPriceBulkDelete.Field()
    shipping_price_update = ShippingPriceUpdate.Field()
    shipping_price_translate = ShippingPriceTranslate.Field()

    shipping_zone_create = ShippingZoneCreate.Field()
    shipping_zone_delete = ShippingZoneDelete.Field()
    shipping_zone_bulk_delete = ShippingZoneBulkDelete.Field()
    shipping_zone_update = ShippingZoneUpdate.Field()
