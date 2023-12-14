from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....channel import models as channel_models
from ....permission.enums import ProductPermissions
from ....warehouse import models
from ....warehouse.error_codes import WarehouseErrorCode
from ....warehouse.validation import validate_warehouse_count
from ...account.i18n import I18nMixin
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import NonNullList, WarehouseError
from ...shipping.types import ShippingZone
from ..types import Warehouse


class WarehouseShippingZoneAssign(ModelMutation, I18nMixin):
    class Meta:
        model = models.Warehouse
        object_type = Warehouse
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        description = "Add shipping zone to given warehouse."
        error_type_class = WarehouseError
        error_type_field = "warehouse_errors"

    class Arguments:
        id = graphene.ID(description="ID of a warehouse to update.", required=True)
        shipping_zone_ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of shipping zone IDs.",
        )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, shipping_zone_ids: list[str]
    ):
        warehouse = cls.get_node_or_error(info, id, only_type=Warehouse)
        shipping_zones = cls.get_nodes_or_error(
            shipping_zone_ids, "shipping_zone_id", only_type=ShippingZone
        )
        cls.clean_shipping_zones(warehouse, shipping_zones)
        warehouse.shipping_zones.add(*shipping_zones)
        return WarehouseShippingZoneAssign(warehouse=warehouse)

    @classmethod
    def clean_shipping_zones(cls, instance, shipping_zones):
        if not validate_warehouse_count(shipping_zones, instance):
            msg = "Shipping zone can be assigned only to one warehouse."
            raise ValidationError(
                {"shipping_zones": msg}, code=WarehouseErrorCode.INVALID.value
            )

        cls.check_if_zones_can_be_assigned(instance, shipping_zones)

    @classmethod
    def check_if_zones_can_be_assigned(cls, instance, shipping_zones):
        """Check if all shipping zones to add has common channel with warehouse.

        Raise and error when the condition is not fulfilled.
        """
        shipping_zone_ids = [zone.id for zone in shipping_zones]
        ChannelShippingZone = channel_models.Channel.shipping_zones.through
        channel_shipping_zones = ChannelShippingZone.objects.filter(
            shippingzone_id__in=shipping_zone_ids
        )

        # shipping zone cannot be assigned when any channel is assigned to the zone
        if not channel_shipping_zones:
            invalid_shipping_zone_ids = shipping_zone_ids

        zone_to_channel_mapping = defaultdict(set)
        for shipping_zone_id, channel_id in channel_shipping_zones.values_list(
            "shippingzone_id", "channel_id"
        ):
            zone_to_channel_mapping[shipping_zone_id].add(channel_id)

        WarehouseChannel = models.Warehouse.channels.through
        zone_channel_ids = set(
            WarehouseChannel.objects.filter(warehouse_id=instance.id).values_list(
                "channel_id", flat=True
            )
        )

        invalid_shipping_zone_ids = cls._find_invalid_shipping_zones(
            zone_to_channel_mapping, shipping_zone_ids, zone_channel_ids
        )

        if invalid_shipping_zone_ids:
            invalid_zones = {
                graphene.Node.to_global_id("ShippingZone", pk)
                for pk in invalid_shipping_zone_ids
            }
            raise ValidationError(
                {
                    "shipping_zones": ValidationError(
                        "Only warehouses that have common channel with shipping zone "
                        "can be assigned.",
                        code=WarehouseErrorCode.INVALID,
                        params={
                            "shipping_zones": invalid_zones,
                        },
                    )
                }
            )

    @staticmethod
    def _find_invalid_shipping_zones(
        zone_to_channel_mapping, shipping_zone_ids, warehouse_channel_ids
    ):
        invalid_warehouse_ids = []
        for zone_id in shipping_zone_ids:
            zone_channels = zone_to_channel_mapping.get(zone_id)
            # shipping zone cannot be added if it hasn't got any channel assigned
            # or if it does not have common channel with the warehouse
            if not zone_channels or not zone_channels.intersection(
                warehouse_channel_ids
            ):
                invalid_warehouse_ids.append(zone_id)
        return invalid_warehouse_ids
