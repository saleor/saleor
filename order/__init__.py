from .models import Order

SESSION_KEY = 'order'

def get_order_from_request(request):
    try:
        return Order.objects.get(token=request.session[SESSION_KEY])
    except (KeyError, Order.DoesNotExist):
        order = Order.objects.create()
        request.session[SESSION_KEY] = order.token

        return order
