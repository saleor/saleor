from collections import defaultdict

from django.db.models import F

from ...order.models import Order, OrderEvent, OrderLine
from ...payment.models import Payment
from ...warehouse.models import Allocation
from ..core.dataloaders import DataLoader


class OrderLinesByVariantIdAndChannelIdLoader(DataLoader):
    context_key = "orderline_by_variant_and_channel"

    def batch_load(self, keys):
        channel_ids = [key[1] for key in keys]
        variant_ids = [key[0] for key in keys]
        order_lines = OrderLine.objects.filter(
            order__channel_id__in=channel_ids, variant_id__in=variant_ids
        ).annotate(channel_id=F("order__channel_id"))

        order_line_by_variant_and_channel_map = defaultdict(list)
        for order_line in order_lines:
            key = (order_line.variant_id, order_line.channel_id)
            order_line_by_variant_and_channel_map[key].append(order_line)
        return [order_line_by_variant_and_channel_map[key] for key in keys]


class OrderByIdLoader(DataLoader):
    context_key = "order_by_id"

    def batch_load(self, keys):
        orders = Order.objects.in_bulk(keys)
        return [orders.get(order_id) for order_id in keys]


class OrderLineByIdLoader(DataLoader):
    context_key = "orderline_by_id"

    def batch_load(self, keys):
        order_lines = OrderLine.objects.in_bulk(keys)
        return [order_lines.get(line_id) for line_id in keys]


class OrderLinesByOrderIdLoader(DataLoader):
    context_key = "orderlines_by_order"

    def batch_load(self, keys):
        lines = OrderLine.objects.filter(order_id__in=keys).order_by("pk")
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.order_id].append(line)
        return [line_map.get(order_id, []) for order_id in keys]


class PaymentsByOrderIdLoader(DataLoader):
    context_key = "payments_by_order"

    def batch_load(self, keys):
        payments = Payment.objects.filter(order_id__in=keys).order_by("pk")
        payment_map = defaultdict(list)
        for payment in payments.iterator():
            payment_map[payment.order_id].append(payment)
        return [payment_map.get(order_id, []) for order_id in keys]


class OrderEventsByOrderIdLoader(DataLoader):
    context_key = "orderevents_by_order"

    def batch_load(self, keys):
        events = OrderEvent.objects.filter(order_id__in=keys).order_by("pk")
        events_map = defaultdict(list)
        for event in events.iterator():
            events_map[event.order_id].append(event)
        return [events_map.get(order_id, []) for order_id in keys]


class AllocationsByOrderLineIdLoader(DataLoader):
    context_key = "allocations_by_orderline_id"

    def batch_load(self, keys):
        allocations = Allocation.objects.filter(order_line__pk__in=keys)
        order_lines_to_allocations = defaultdict(list)

        for allocation in allocations:
            order_lines_to_allocations[allocation.order_line_id].append(allocation)

        return [order_lines_to_allocations[order_line_id] for order_line_id in keys]
