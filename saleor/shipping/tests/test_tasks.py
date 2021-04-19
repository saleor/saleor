from ...checkout.models import Checkout
from ...order import OrderStatus
from ...order.models import Order
from ..tasks import drop_invalid_shipping_methods_relations_for_given_channels


def test_drop_invalid_shipping_method_relations(
    checkouts_list,
    order_list,
    shipping_method,
    other_shipping_method,
    shipping_method_weight_based,
    channel_USD,
    channel_PLN,
):
    # given
    # given
    checkout_PLN = checkouts_list[0]
    checkout_PLN.shipping_method = shipping_method
    checkout_PLN.channel = channel_PLN

    checkout_USD = checkouts_list[1]
    checkout_USD.shipping_method = shipping_method
    checkout_USD.channel = channel_USD

    checkout_weight_shipping_method = checkouts_list[2]
    checkout_weight_shipping_method.shipping_method = shipping_method_weight_based
    checkout_weight_shipping_method.channel = channel_USD

    checkout_another_shipping_method = checkouts_list[3]
    checkout_another_shipping_method.shipping_method = other_shipping_method
    checkout_another_shipping_method.channel = channel_USD

    Checkout.objects.bulk_update(
        [
            checkout_PLN,
            checkout_USD,
            checkout_weight_shipping_method,
            checkout_another_shipping_method,
        ],
        ["shipping_method", "channel"],
    )

    order_confirmed = order_list[0]
    order_confirmed.status = OrderStatus.UNFULFILLED
    order_confirmed.shipping_method = shipping_method
    order_confirmed.channel = channel_USD

    order_draft = order_list[1]
    order_draft.status = OrderStatus.DRAFT
    order_draft.shipping_method = shipping_method
    order_draft.channel = channel_USD

    order_draft_PLN = order_list[2]
    order_draft_PLN.status = OrderStatus.DRAFT
    order_draft_PLN.shipping_method = shipping_method
    order_draft_PLN.channel = channel_PLN

    Order.objects.bulk_update(
        [order_confirmed, order_draft, order_draft_PLN],
        ["status", "shipping_method", "channel"],
    )

    # when
    drop_invalid_shipping_methods_relations_for_given_channels(
        [shipping_method.id, other_shipping_method.id], [channel_USD.id]
    )

    # then
    checkout_PLN.refresh_from_db()
    checkout_USD.refresh_from_db()
    checkout_another_shipping_method.refresh_from_db()

    assert checkout_PLN.shipping_method == shipping_method
    assert checkout_USD.shipping_method is None
    assert (
        checkout_weight_shipping_method.shipping_method == shipping_method_weight_based
    )
    assert checkout_another_shipping_method.shipping_method is None

    order_confirmed.refresh_from_db()
    order_draft.refresh_from_db()
    order_draft_PLN.refresh_from_db()

    assert order_confirmed.shipping_method == shipping_method
    assert order_draft.shipping_method is None
    assert order_draft_PLN.shipping_method == shipping_method
