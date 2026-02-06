from collections import defaultdict
from collections.abc import Iterable
from typing import cast
from uuid import UUID

from django.db.models import F
from promise import Promise

from ...core.db.connection import allow_writer_in_context
from ...order.calculations import (
    get_expired_line_ids,
    prepare_order_lines_for_refresh,
    process_order_prices,
    process_order_promotion,
    should_refresh_prices,
)
from ...order.delivery_context import get_valid_shipping_methods_for_order
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
from ...shipping.interface import ShippingMethodData
from ...warehouse.models import Allocation
from ..app.dataloaders.utils import get_app_promise
from ..channel.dataloaders.by_self import ChannelByIdLoader
from ..core.dataloaders import DataLoader
from ..plugins.dataloaders import (
    plugin_manager_promise,
)
from ..shipping.dataloaders import (
    ShippingMethodChannelListingByChannelSlugLoader,
)
from ..utils import get_user_or_app_from_context


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


class OrderByIdLoader(DataLoader[UUID, Order]):
    context_key = "order_by_id"

    def batch_load(self, keys):
        orders = Order.objects.using(self.database_connection_name).in_bulk(keys)
        return [orders.get(order_id) for order_id in keys]


class OrderByNumberLoader(DataLoader[str, Order]):
    context_key = "order_by_number"

    def batch_load(self, keys):
        orders = (
            Order.objects.using(self.database_connection_name)
            .filter(number__in=keys)
            .in_bulk(field_name="number")
        )
        return [orders.get(number) for number in keys]


class OrdersByUserLoader(DataLoader[int, list[Order]]):
    context_key = "order_by_user"

    def batch_load(self, keys):
        orders = Order.objects.using(self.database_connection_name).filter(
            user_id__in=keys
        )
        orders_by_user_map = defaultdict(list)
        for order in orders:
            orders_by_user_map[order.user_id].append(order)
        return [orders_by_user_map.get(user_id, []) for user_id in keys]


class OrderLineByIdLoader(DataLoader[UUID, OrderLine]):
    context_key = "orderline_by_id"

    def batch_load(self, keys):
        order_lines = OrderLine.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [order_lines.get(line_id) for line_id in keys]


class OrderLinesByOrderIdLoader(DataLoader[UUID, list[OrderLine]]):
    context_key = "orderlines_by_order"

    def batch_load(self, keys):
        lines = (
            OrderLine.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("created_at")
        )
        line_map = defaultdict(list)
        for line in lines.iterator(chunk_size=1000):
            line_map[line.order_id].append(line)
        return [line_map.get(order_id, []) for order_id in keys]


class OrderEventsByOrderIdLoader(DataLoader[UUID, list[OrderEvent]]):
    context_key = "orderevents_by_order"

    def batch_load(self, keys):
        events = (
            OrderEvent.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        events_map = defaultdict(list)
        for event in events.iterator(chunk_size=1000):
            events_map[event.order_id].append(event)
        return [events_map.get(order_id, []) for order_id in keys]


class OrderEventsByIdLoader(DataLoader[int, OrderEvent]):
    context_key = "orderevents_by_id"

    def batch_load(self, keys):
        events = (
            OrderEvent.objects.using(self.database_connection_name)
            .filter(id__in=keys)
            .in_bulk()
        )
        return [events.get(event_id) for event_id in keys]


class OrderGrantedRefundsByOrderIdLoader(DataLoader[UUID, list[OrderGrantedRefund]]):
    context_key = "order_granted_refunds_by_order_id"

    def batch_load(self, keys):
        refunds = OrderGrantedRefund.objects.using(
            self.database_connection_name
        ).filter(order_id__in=keys)
        refunds_map = defaultdict(list)

        for refund in refunds.iterator(chunk_size=1000):
            refunds_map[refund.order_id].append(refund)
        return [refunds_map.get(order_id, []) for order_id in keys]


class OrderGrantedRefundLinesByOrderGrantedRefundIdLoader(
    DataLoader[int, list[OrderGrantedRefundLine]]
):
    context_key = "order_granted_refund_lines_by_granted_refund_id"

    def batch_load(self, keys):
        refund_lines = OrderGrantedRefundLine.objects.using(
            self.database_connection_name
        ).filter(granted_refund_id__in=keys)
        refund_lines_map = defaultdict(list)

        for refund_line in refund_lines.iterator(chunk_size=1000):
            refund_lines_map[refund_line.granted_refund_id].append(refund_line)
        return [
            refund_lines_map.get(granted_refund_id, []) for granted_refund_id in keys
        ]


class AllocationsByOrderLineIdLoader(DataLoader[UUID, list[Allocation]]):
    context_key = "allocations_by_orderline_id"

    def batch_load(self, keys):
        allocations = Allocation.objects.using(self.database_connection_name).filter(
            order_line__pk__in=keys
        )
        order_lines_to_allocations = defaultdict(list)

        for allocation in allocations:
            order_lines_to_allocations[allocation.order_line_id].append(allocation)

        return [order_lines_to_allocations[order_line_id] for order_line_id in keys]


class FulfillmentsByOrderIdLoader(DataLoader[UUID, list[Fulfillment]]):
    context_key = "fulfillments_by_order"

    def batch_load(self, keys):
        fulfillments = (
            Fulfillment.objects.using(self.database_connection_name)
            .filter(order_id__in=keys)
            .order_by("pk")
        )
        fulfillments_map = defaultdict(list)
        for fulfillment in fulfillments.iterator(chunk_size=1000):
            fulfillments_map[fulfillment.order_id].append(fulfillment)
        return [fulfillments_map.get(order_id, []) for order_id in keys]


class FulfillmentLinesByIdLoader(DataLoader[int, FulfillmentLine]):
    context_key = "fulfillment_lines_by_id"

    def batch_load(self, keys):
        fulfillment_lines = FulfillmentLine.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [fulfillment_lines.get(line_id) for line_id in keys]


class FulfillmentLinesByFulfillmentIdLoader(DataLoader[int, list[FulfillmentLine]]):
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


class TransactionItemsByOrderIDLoader(DataLoader[UUID, list[TransactionItem]]):
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


class TransactionEventsByOrderGrantedRefundIdLoader(
    DataLoader[int, list[TransactionEvent]]
):
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


class OrderPromotionCalculateByOrderIdLoaderAndWebhookSyncLoader(
    DataLoader[tuple[UUID, bool], tuple[Order, Iterable[OrderLine]]]
):
    context_key = "order_promotion_calculate_by_order_id_and_webhook_sync"

    def batch_load(self, keys):
        orders_loader = OrderByIdLoader(self.context).load_many(
            [order_id for order_id, _ in keys]
        )
        lines_loader = OrderLinesByOrderIdLoader(self.context).load_many(
            [order_id for order_id, _ in keys]
        )

        current_lines_ids_per_order: dict[UUID, set[UUID]] = {}

        def refresh_lines(data: list[tuple[Order, list[OrderLine]]]):
            for order, _order_lines in data:
                if order is None:
                    continue

                if order.id not in current_lines_ids_per_order:
                    continue
                if current_lines_ids_per_order[order.id] != {
                    line.id for line in _order_lines
                }:
                    # While re-calculating the prices, the order lines might have been
                    # changed (gift promotions). In that case, we need to refresh
                    # the order lines in dataloader cache to make sure that the
                    # rest of the code works with up-to-date data.
                    OrderLinesByOrderIdLoader(self.context).clear(order.id)
                    OrderLinesByOrderIdLoader(self.context).prime(
                        order.id, _order_lines
                    )
            return data

        def calculate_prices(data):
            orders, lines = data
            results: list[Promise[tuple[Order | None, Iterable[OrderLine]]]] = []
            for order, order_lines, (_, allow_sync_webhooks) in zip(
                orders, lines, keys, strict=True
            ):
                if order is None:
                    results.append(Promise.resolve((None, [])))
                    continue
                order = cast(Order, order)

                expired_line_ids = get_expired_line_ids(order, order_lines)
                if not should_refresh_prices(
                    order=order,
                    force_update=False,
                    expired_line_ids=expired_line_ids,
                    database_connection_name=self.database_connection_name,
                    allow_sync_webhooks=allow_sync_webhooks,
                ):
                    results.append(Promise.resolve((order, order_lines)))
                    continue

                lines_info = prepare_order_lines_for_refresh(
                    order=order,
                    lines=order_lines,
                    expired_line_ids=expired_line_ids,
                    database_connection_name=self.database_connection_name,
                )
                if lines_info is None:
                    results.append(Promise.resolve((order, order_lines)))
                    continue

                process_order_promotion(
                    order,
                    lines_info,
                    database_connection_name=self.database_connection_name,
                )
                refreshed_lines = [line_info.line for line_info in lines_info]
                current_lines_ids_per_order[order.id] = {
                    line.id for line in refreshed_lines
                }

                results.append(Promise.resolve((order, refreshed_lines)))
            return Promise.all(results).then(refresh_lines)

        return Promise.all([orders_loader, lines_loader]).then(calculate_prices)


class OrderPriceCalculationByOrderIdAndWebhookSyncLoader(
    DataLoader[tuple[UUID, bool], tuple[Order, Iterable[OrderLine]]]
):
    context_key = "order_price_calculation_by_order_id_and_webhook_sync"

    def batch_load(self, keys):
        def with_updated_promotions(
            data,
        ):
            app, orders_and_lines = data

            def calculate_prices(manager):
                results: list[Promise[tuple[Order, Iterable[OrderLine]]]] = []
                for (order, lines), (_, allow_sync_webhooks) in zip(
                    orders_and_lines, keys, strict=True
                ):
                    expired_line_ids = get_expired_line_ids(order, lines)
                    if not should_refresh_prices(
                        order=order,
                        force_update=False,
                        expired_line_ids=expired_line_ids,
                        database_connection_name=self.database_connection_name,
                        allow_sync_webhooks=allow_sync_webhooks,
                    ):
                        results.append(Promise.resolve((order, lines)))
                        continue
                    result = process_order_prices(
                        order=order,
                        manager=manager,
                        requestor=app or self.context.user,
                        lines=lines,
                        database_connection_name=self.database_connection_name,
                    )
                    results.append(result)
                return Promise.all(results)

            return plugin_manager_promise(self.context, app).then(calculate_prices)

        return Promise.all(
            [
                get_app_promise(self.context),
                OrderPromotionCalculateByOrderIdLoaderAndWebhookSyncLoader(
                    self.context
                ).load_many(keys),
            ]
        ).then(with_updated_promotions)


class OrderShippingMethodsByOrderIdAndWebhookSyncLoader(
    DataLoader[tuple[UUID, bool], list[ShippingMethodData]]
):
    context_key = "order_shipping_methods_by_order"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        orders = OrderByIdLoader(self.context).load_many([order for (order, _) in keys])

        def with_orders(orders: list[Order]):
            def with_listings(channel_listings):
                results: list[Promise[list[ShippingMethodData]]] = []
                with allow_writer_in_context(self.context):
                    for order, listings, (_, allow_sync_webhooks) in zip(
                        orders, channel_listings, keys, strict=True
                    ):
                        result = get_valid_shipping_methods_for_order(
                            order,
                            listings,
                            requestor=requestor,
                            database_connection_name=self.database_connection_name,
                            allow_sync_webhooks=allow_sync_webhooks,
                        )
                    results.append(result)
                return Promise.all(results)

            def with_channels(channels):
                return (
                    ShippingMethodChannelListingByChannelSlugLoader(self.context)
                    .load_many([c.slug for c in channels])
                    .then(with_listings)
                )

            return (
                ChannelByIdLoader(self.context)
                .load_many([order.channel_id for order in orders if order is not None])
                .then(with_channels)
            )

        return orders.then(with_orders)
