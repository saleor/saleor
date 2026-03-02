from collections import defaultdict
from uuid import UUID

from ...inventory.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderRequestedAllocation,
)
from ..core.dataloaders import DataLoader


class PurchaseOrderByIdLoader(DataLoader[int, PurchaseOrder]):
    context_key = "purchase_order_by_id"

    def batch_load(self, keys):
        purchase_orders = PurchaseOrder.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [purchase_orders.get(purchase_order_id) for purchase_order_id in keys]


class PurchaseOrdersByOrderIdLoader(DataLoader[UUID, list[PurchaseOrder]]):
    context_key = "purchase_orders_by_order_id"

    def batch_load(self, keys):
        pora_qs = (
            PurchaseOrderRequestedAllocation.objects.using(
                self.database_connection_name
            )
            .filter(allocation__order_line__order_id__in=keys)
            .values_list("allocation__order_line__order_id", "purchase_order_id")
            .distinct()
        )

        order_to_po_ids = defaultdict(set)
        for order_id, po_id in pora_qs:
            order_to_po_ids[order_id].add(po_id)

        all_po_ids = {po_id for po_ids in order_to_po_ids.values() for po_id in po_ids}
        purchase_orders = PurchaseOrder.objects.using(
            self.database_connection_name
        ).in_bulk(list(all_po_ids))

        return [
            [
                purchase_orders[po_id]
                for po_id in order_to_po_ids.get(order_id, set())
                if po_id in purchase_orders
            ]
            for order_id in keys
        ]


class PurchaseOrderItemByIdLoader(DataLoader[int, PurchaseOrderItem]):
    context_key = "purchase_order_item_by_id"

    def batch_load(self, keys):
        items = PurchaseOrderItem.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [items.get(item_id) for item_id in keys]
