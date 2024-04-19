from collections import defaultdict
from collections.abc import Iterable
from typing import cast

from django.db.models import F

from ...order.models import (
    Fulfillment,
    FulfillmentLine,
    Order,
    OrderEvent,
    OrderGrantedRefund,
    OrderGrantedRefundLine,
    OrderLine,
)
from ...payment.models import TransactionEvent, TransactionItem
from ...warehouse.models import Allocation
from ..core.dataloaders import DataLoader


class OrderLinesByVariantIdAndChannelIdLoader(
    DataLoader[tuple[int, int], list[OrderLine]]
):
    context_key = "orderline_by_variant_and_channel"

    def batch_load(self, keys: Iterable[tuple[int, int]]):
        channel_ids = [key[1] for key in keys]
        variant_ids = [key[0] for key in keys]
        order_lines = (
            OrderLine.objects.using(self.database_connection_name)
            .filter(order__channel_id__in=channel_ids, variant_id__in=variant_ids)
            .annotate(channel_id=F("order__channel_id"))
            .order_by("created_at", "id")
        )

        order_line_by_variant_and_channel_map: defaultdict[
            tuple[int, int], list[OrderLine]
        ] = defaultdict(list)
        for order_line in order_lines:
            key = (
                cast(int, order_line.variant_id),
                getattr(order_line, "channel_id", 0),  # annotation
            )
            order_line_by_variant_and_channel_map[key].append(order_line)
        return [order_line_by_variant_and_channel_map[key] for key in keys]


class OrderByIdLoader(DataLoader):
    context_key = "order_by_id"

    def batch_load(self, keys):
        orders = Order.objects.using(self.database_connection_name).in_bulk(keys)
        return [orders.get(order_id) for order_id in keys]


class OrderByNumberLoader(DataLoader):
    context_key = "order_by_number"

    def batch_load(self, keys):
        orders = (
            Order.objects.using(self.database_connection_name)
            .filter(number__in=keys)
            .in_bulk(field_name="number")
        )
        return [orders.get(number) for number in keys]


class OrdersByUserLoader(DataLoader):
    context_key = "order_by_user"

    def batch_load(self, keys):
        orders = Order.objects.using(self.database_connection_name).filter(
            user_id__in=keys
        )
        orders_by_user_map = defaultdict(list)
        for order in orders:
            orders_by_user_map[order.user_id].append(order)
        return [orders_by_user_map.get(user_id, []) for user_id in keys]


class OrderLineByIdLoader(DataLoader):
    context_key = "orderline_by_id"

    def batch_load(self, keys):
        order_lines = OrderLine.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [order_lines.get(line_id) for line_id in keys]


class OrderLinesByOrderIdLoader(DataLoader):
    context_key = "orderlines_by_order"

    def batch_load(self, keys):
        lines = (
            OrderLine.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("created_at")
        )
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.order_id].append(line)
        return [line_map.get(order_id, []) for order_id in keys]


class OrderEventsByOrderIdLoader(DataLoader):
    context_key = "orderevents_by_order"

    def batch_load(self, keys):
        events = (
            OrderEvent.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        events_map = defaultdict(list)
        for event in events.iterator():
            events_map[event.order_id].append(event)
        return [events_map.get(order_id, []) for order_id in keys]


class OrderEventsByIdLoader(DataLoader):
    context_key = "orderevents_by_id"

    def batch_load(self, keys):
        events = (
            OrderEvent.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .in_bulk()
        )
        return [events.get(event_id) for event_id in keys]


class OrderGrantedRefundsByOrderIdLoader(DataLoader):
    context_key = "order_granted_refunds_by_order_id"

    def batch_load(self, keys):
        refunds = OrderGrantedRefund.objects.using(
            self.database_connection_name
        ).filter(order_id__in=keys)
        refunds_map = defaultdict(list)

        for refund in refunds.iterator():
            refunds_map[refund.order_id].append(refund)
        return [refunds_map.get(order_id, []) for order_id in keys]


class OrderGrantedRefundLinesByOrderGrantedRefundIdLoader(DataLoader):
    context_key = "order_granted_refund_lines_by_granted_refund_id"

    def batch_load(self, keys):
        refund_lines = OrderGrantedRefundLine.objects.using(
            self.database_connection_name
        ).filter(granted_refund_id__in=keys)
        refund_lines_map = defaultdict(list)

        for refund_line in refund_lines.iterator():
            refund_lines_map[refund_line.granted_refund_id].append(refund_line)
        return [
            refund_lines_map.get(granted_refund_id, []) for granted_refund_id in keys
        ]


class AllocationsByOrderLineIdLoader(DataLoader):
    context_key = "allocations_by_orderline_id"

    def batch_load(self, keys):
        allocations = Allocation.objects.using(self.database_connection_name).filter(
            order_line__pk__in=keys
        )
        order_lines_to_allocations = defaultdict(list)

        for allocation in allocations:
            order_lines_to_allocations[allocation.order_line_id].append(allocation)

        return [order_lines_to_allocations[order_line_id] for order_line_id in keys]


class FulfillmentsByOrderIdLoader(DataLoader):
    context_key = "fulfillments_by_order"

    def batch_load(self, keys):
        fulfillments = (
            Fulfillment.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        fulfillments_map = defaultdict(list)
        for fulfillment in fulfillments.iterator():
            fulfillments_map[fulfillment.order_id].append(fulfillment)
        return [fulfillments_map.get(order_id, []) for order_id in keys]


class FulfillmentLinesByIdLoader(DataLoader):
    context_key = "fulfillment_lines_by_id"

    def batch_load(self, keys):
        fulfillment_lines = FulfillmentLine.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [fulfillment_lines.get(line_id) for line_id in keys]


class FulfillmentLinesByFulfillmentIdLoader(DataLoader):
    context_key = "fulfillment_lines_by_fulfillment_id"

    def batch_load(self, keys):
        fulfillment_lines = (
            FulfillmentLine.objects.using(self.database_connection_name)
            .filter(fulfillment_id__in=keys)
            .order_by("pk")
        )
        fulfillment_lines_map = defaultdict(list)

        for fulfillment_line in fulfillment_lines:
            fulfillment_lines_map[fulfillment_line.fulfillment_id].append(
                fulfillment_line
            )

        return [
            fulfillment_lines_map.get(fulfillment_id, []) for fulfillment_id in keys
        ]


class TransactionItemsByOrderIDLoader(DataLoader):
    context_key = "transaction_items_by_order_id"

    def batch_load(self, keys):
        transactions = (
            TransactionItem.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        transactions_map = defaultdict(list)
        for transaction in transactions:
            transactions_map[transaction.order_id].append(transaction)
        return [transactions_map.get(order_id, []) for order_id in keys]


class TransactionEventsByOrderGrantedRefundIdLoader(DataLoader):
    context_key = "transaction_event_by_order_granted_refund_id"

    def batch_load(self, keys):
        events = (
            TransactionEvent.objects.using(self.database_connection_name)
            .filter(related_granted_refund__in=keys)
            .order_by("-created_at")
        )
        event_map = defaultdict(list)
        for event in events:
            event_map[event.related_granted_refund_id].append(event)
        return [event_map.get(granted_refund_id, []) for granted_refund_id in keys]
