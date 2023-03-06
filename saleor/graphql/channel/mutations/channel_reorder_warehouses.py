from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import ChannelPermissions
from ....core.tracing import traced_atomic_transaction
from ...core.descriptions import ADDED_IN_37, PREVIEW_FEATURE
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation
from ...core.types import ChannelError, ChannelErrorCode, NonNullList
from ...core.utils.reordering import perform_reordering
from ...warehouse.types import Warehouse
from ..types import Channel


class ChannelReorderWarehouses(BaseMutation):
    channel = graphene.Field(
        Channel, description="Channel within the warehouses are reordered."
    )

    class Arguments:
        channel_id = graphene.ID(
            description="ID of a channel.",
            required=True,
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description=(
                "The list of reordering operations for the given channel warehouses."
            ),
        )

    class Meta:
        description = (
            "Reorder the warehouses of a channel." + ADDED_IN_37 + PREVIEW_FEATURE
        )
        permissions = (ChannelPermissions.MANAGE_CHANNELS,)
        error_type_class = ChannelError

    @classmethod
    def perform_mutation(cls, _root, info, channel_id, moves):
        channel = cls.get_node_or_error(
            info, channel_id, field="channel_id", only_type=Channel
        )

        warehouses_m2m = channel.channelwarehouse
        operations = cls.get_operations(moves, warehouses_m2m)

        with traced_atomic_transaction():
            perform_reordering(warehouses_m2m, operations)

        return ChannelReorderWarehouses(channel=channel)

    @classmethod
    def get_operations(cls, moves, channel_warehouses_m2m):
        warehouse_ids = [move["id"] for move in moves]
        warehouse_pks = cls.get_global_ids_or_error(
            warehouse_ids, only_type=Warehouse, field="moves"
        )

        warehouses_m2m = channel_warehouses_m2m.filter(warehouse_id__in=warehouse_pks)

        if warehouses_m2m.count() != len(set(warehouse_pks)):
            pks = {
                str(pk) for pk in warehouses_m2m.values_list("warehouse_id", flat=True)
            }
            invalid_values = set(warehouse_pks) - pks
            invalid_ids = [
                graphene.Node.to_global_id("Warehouse", warehouse_id)
                for warehouse_id in invalid_values
            ]
            raise ValidationError(
                {
                    "moves": ValidationError(
                        "Couldn't resolve to a warehouse",
                        code=ChannelErrorCode.NOT_FOUND,
                        params={"warehouses": invalid_ids},
                    )
                }
            )

        warehouse_id_to_warehouse_m2m_id = {
            str(warehouse_data["warehouse_id"]): warehouse_data["id"]
            for warehouse_data in warehouses_m2m.values("id", "warehouse_id")
        }
        operations = defaultdict(int)
        for warehouse_pk, move in zip(warehouse_pks, moves):
            warehouse_m2m_id = warehouse_id_to_warehouse_m2m_id[warehouse_pk]
            operations[warehouse_m2m_id] += move.sort_order

        return dict(operations)
