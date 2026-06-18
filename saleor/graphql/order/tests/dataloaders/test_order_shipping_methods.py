import uuid

from .....shipping.interface import ShippingMethodData
from ....context import SaleorContext
from ...dataloaders import OrderShippingMethodsByOrderIdAndWebhookSyncLoader


def _build_context():
    context = SaleorContext()
    context.app = None
    context.user = None
    context.allow_replica = False
    return context


def test_batch_load_single_order(order_with_lines):
    # given
    order = order_with_lines
    keys = [(order.id, True)]
    context = _build_context()
    loader = OrderShippingMethodsByOrderIdAndWebhookSyncLoader(context)

    # when
    result = loader.batch_load(keys).get()

    # then
    assert len(result) == 1
    assert all(isinstance(method, ShippingMethodData) for method in result[0])


def test_batch_load_missing_order_returns_empty_list(order_with_lines):
    # given
    # key references an order that does not exist, so the loader resolves it to None
    missing_order_id = uuid.uuid4()
    keys = [(missing_order_id, True)]
    context = _build_context()
    loader = OrderShippingMethodsByOrderIdAndWebhookSyncLoader(context)

    # when
    result = loader.batch_load(keys).get()

    # then
    assert len(result) == 1
    assert result[0] == []


def test_batch_load_mixed_existing_and_missing_orders(order_with_lines):
    # given
    order = order_with_lines
    missing_order_id = uuid.uuid4()
    keys = [(missing_order_id, True), (order.id, True)]
    context = _build_context()
    loader = OrderShippingMethodsByOrderIdAndWebhookSyncLoader(context)

    # when
    result = loader.batch_load(keys).get()

    # then
    assert len(result) == len(keys)
    assert result[0] == []
    assert all(isinstance(method, ShippingMethodData) for method in result[1])
