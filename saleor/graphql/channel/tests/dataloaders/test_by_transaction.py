from .....channel.models import Channel
from ....context import SaleorContext
from ...dataloaders.by_transaction import ChannelByTransactionIdLoader


def test_batch_load_with_order_transactions(
    order_with_lines, transaction_item_generator
):
    # given
    order = order_with_lines
    transaction1 = transaction_item_generator(order_id=order.id, checkout_id=None)
    transaction2 = transaction_item_generator(order_id=order.id, checkout_id=None)

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([transaction1.id, transaction2.id]).get()

    # then
    assert len(channels) == 2
    assert channels[0] == order.channel
    assert channels[1] == order.channel
    assert all(isinstance(channel, Channel) for channel in channels)


def test_batch_load_with_checkout_transactions(checkout, transaction_item_generator):
    # given
    transaction1 = transaction_item_generator(checkout_id=checkout.token, order_id=None)
    transaction2 = transaction_item_generator(checkout_id=checkout.token, order_id=None)

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([transaction1.id, transaction2.id]).get()

    # then
    assert len(channels) == 2
    assert channels[0] == checkout.channel
    assert channels[1] == checkout.channel
    assert all(isinstance(channel, Channel) for channel in channels)


def test_batch_load_with_mixed_transactions(
    order_with_lines, checkout, transaction_item_generator
):
    # given
    order = order_with_lines
    order_transaction = transaction_item_generator(order_id=order.id, checkout_id=None)
    checkout_transaction = transaction_item_generator(
        checkout_id=checkout.token, order_id=None
    )

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([order_transaction.id, checkout_transaction.id]).get()

    # then
    assert len(channels) == 2
    assert channels[0] == order.channel
    assert channels[1] == checkout.channel


def test_batch_load_with_nonexistent_transaction_ids():
    # given
    nonexistent_ids = [99999, 88888]

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load(nonexistent_ids).get()

    # then
    assert len(channels) == 2
    assert channels[0] is None
    assert channels[1] is None


def test_batch_load_with_transaction_without_order_or_checkout(
    transaction_item_generator,
):
    # given - transaction with neither order_id nor checkout_id
    transaction = transaction_item_generator(order_id=None, checkout_id=None)

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([transaction.id]).get()

    # then
    assert len(channels) == 1
    assert channels[0] is None


def test_batch_load_empty_keys():
    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([]).get()

    # then
    assert channels == []


def test_batch_load_with_deleted_order(order_with_lines, transaction_item_generator):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.id, checkout_id=None)
    transaction_id = transaction.id
    # Delete transaction first, then order to avoid protected foreign key constraint
    transaction.delete()
    order.delete()

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([transaction_id]).get()

    # then
    assert len(channels) == 1
    assert channels[0] is None


def test_batch_load_with_deleted_checkout(checkout, transaction_item_generator):
    # given
    transaction = transaction_item_generator(checkout_id=checkout.token, order_id=None)
    checkout.delete()

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    channels = loader.batch_load([transaction.id]).get()

    # then
    assert len(channels) == 1
    assert channels[0] is None


def test_batch_load_maintains_order(
    order_with_lines, checkout, transaction_item_generator
):
    # given
    order = order_with_lines
    transaction1 = transaction_item_generator(order_id=order.id, checkout_id=None)
    transaction2 = transaction_item_generator(checkout_id=checkout.token, order_id=None)
    transaction3 = transaction_item_generator(order_id=order.id, checkout_id=None)

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    # Request in specific order
    channels = loader.batch_load(
        [transaction2.id, transaction1.id, transaction3.id]
    ).get()

    # then
    assert len(channels) == 3
    # Results should match the order of request
    assert channels[0] == checkout.channel  # transaction2 -> checkout
    assert channels[1] == order.channel  # transaction1 -> order
    assert channels[2] == order.channel  # transaction3 -> order


def test_batch_load_handles_duplicate_transaction_ids(
    order_with_lines, transaction_item_generator
):
    # given
    order = order_with_lines
    transaction = transaction_item_generator(order_id=order.id, checkout_id=None)

    # when
    context = SaleorContext()
    loader = ChannelByTransactionIdLoader(context)
    # Request same transaction ID multiple times
    channels = loader.batch_load([transaction.id, transaction.id, transaction.id]).get()

    # then
    assert len(channels) == 3
    assert all(channel == order.channel for channel in channels)
