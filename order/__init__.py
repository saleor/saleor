from .models import Order

SESSION_KEY = 'order'

def get_order_from_request(request):
    try:
        return request.session[SESSION_KEY]
    except KeyError:
        request.session[SESSION_KEY] = Order.objects.create()
        return request.session[SESSION_KEY]
