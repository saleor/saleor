from .models import Order
from cart import CartPartitioner

SESSION_KEY = 'order'


def get_order_from_request(request, cart):
    try:
        return Order.objects.get(token=request.session[SESSION_KEY])
    except (KeyError, Order.DoesNotExist):
        partitioner = CartPartitioner(cart)
        order = Order.objects.create_from_partitions(partitioner)
        request.session[SESSION_KEY] = order.token

        return order
