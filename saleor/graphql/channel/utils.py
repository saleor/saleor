from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q
from django.utils.functional import SimpleLazyObject
from graphql.error import GraphQLError

from ...channel.exceptions import ChannelNotDefined, NoDefaultChannel
from ...channel.models import Channel
from ...channel.utils import get_default_channel
from ...shipping.models import ShippingZone


def get_default_channel_slug_or_graphql_error(
    allow_replica: bool = False,
) -> SimpleLazyObject:
    """Return a default channel slug in lazy way or a GraphQL error.

    Utility to get the default channel in GraphQL query resolvers.
    """
    return SimpleLazyObject(
        lambda: get_default_channel_or_graphql_error(allow_replica).slug
    )


def get_default_channel_or_graphql_error(allow_replica: bool = False) -> Channel:
    """Return a default channel or a GraphQL error.

    Utility to get the default channel in GraphQL query resolvers.
    """
    try:
        channel = get_default_channel(allow_replica)
    except (ChannelNotDefined, NoDefaultChannel) as e:
        raise GraphQLError(str(e))
    else:
        return channel


def validate_channel(channel_slug, error_class):
    try:
        channel = Channel.objects.get(slug=channel_slug)
    except Channel.DoesNotExist:
        raise ValidationError(
            {
                "channel": ValidationError(
                    f"Channel with '{channel_slug}' slug does not exist.",
                    code=error_class.NOT_FOUND.value,
                )
            }
        )
    if not channel.is_active:
        raise ValidationError(
            {
                "channel": ValidationError(
                    f"Channel with '{channel_slug}' is inactive.",
                    code=error_class.CHANNEL_INACTIVE.value,
                )
            }
        )
    return channel


def clean_channel(
    channel_slug,
    error_class,
    allow_replica: bool = False,
):
    if channel_slug is not None:
        channel = validate_channel(channel_slug, error_class)
    else:
        try:
            channel = get_default_channel(allow_replica)
        except ChannelNotDefined:
            raise ValidationError(
                {
                    "channel": ValidationError(
                        "You need to provide channel slug.",
                        code=error_class.MISSING_CHANNEL_SLUG.value,
                    )
                }
            )
    return channel


def delete_invalid_warehouse_to_shipping_zone_relations(
    channel, warehouse_ids, shipping_zone_ids=None, channel_deletion=False
):
    """Delete not valid warehouse-zone relations after channel updates.

    Look up for warehouse to shipping zone relations that will not have common channels
    after unlinking the given channel from warehouses or shipping zones.
    The warehouse can be linked with shipping zone only if common channel exists.
    """
    shipping_zone_ids = shipping_zone_ids or []

    ChannelWarehouse = Channel.warehouses.through
    ShippingZoneWarehouse = ShippingZone.warehouses.through
    ShippingZoneChannel = ShippingZone.channels.through

    shipping_zone_warehouses = ShippingZoneWarehouse.objects.filter(
        Q(warehouse_id__in=warehouse_ids) | Q(shippingzone_id__in=shipping_zone_ids)
    )
    channel_warehouses = ChannelWarehouse.objects.filter(
        Exists(shipping_zone_warehouses.filter(warehouse_id=OuterRef("warehouse_id")))
    )
    shipping_zone_channels = ShippingZoneChannel.objects.filter(
        Exists(
            shipping_zone_warehouses.filter(shippingzone_id=OuterRef("shippingzone_id"))
        )
    )

    warehouse_to_channel_ids = _get_warehouse_to_channels_mapping(
        channel, channel_warehouses, channel_deletion
    )
    zone_to_channel_ids = _get_shipping_zone_to_channels_mapping(shipping_zone_channels)
    shipping_zone_warehouses_to_delete = _get_invalid_shipping_zone_warehouses_ids(
        shipping_zone_warehouses, warehouse_to_channel_ids, zone_to_channel_ids
    )

    # delete invalid shipping zone - warehouse relations
    ShippingZoneWarehouse.objects.filter(
        id__in=shipping_zone_warehouses_to_delete
    ).delete()


def _get_warehouse_to_channels_mapping(channel, channel_warehouses, channel_deletion):
    warehouse_to_channel_ids = defaultdict(set)
    for warehouse_id, channel_id in channel_warehouses.values_list(
        "warehouse_id", "channel_id"
    ):
        # when the channel will be deleted so we do not want this channel in warehouse
        # channels set
        if not channel_deletion or channel_id != channel.id:
            warehouse_to_channel_ids[warehouse_id].add(channel_id)
    return warehouse_to_channel_ids


def _get_shipping_zone_to_channels_mapping(shipping_zone_channels):
    zone_to_channel_ids = defaultdict(set)
    for zone_id, channel_id in shipping_zone_channels.values_list(
        "shippingzone_id", "channel_id"
    ):
        zone_to_channel_ids[zone_id].add(channel_id)
    return zone_to_channel_ids


def _get_invalid_shipping_zone_warehouses_ids(
    shipping_zone_warehouses, warehouse_to_channel_ids, zone_to_channel_ids
):
    shipping_zone_warehouses_to_delete = []
    for id, zone_id, warehouse_id in shipping_zone_warehouses.values_list(
        "id", "shippingzone_id", "warehouse_id"
    ):
        warehouse_channels = warehouse_to_channel_ids.get(warehouse_id, set())
        zone_channels = zone_to_channel_ids.get(zone_id, set())
        # if there is no common channels between shipping zone and warehouse
        # the relation should be deleted
        if not warehouse_channels.intersection(zone_channels):
            shipping_zone_warehouses_to_delete.append(id)
    return shipping_zone_warehouses_to_delete
