from ...product.models import Product
from ...order.models import Order
from ...userprofile.models import User


def search(phrase):
    return {'products': Product.objects.none(),
            'orders': Order.objects.none(),
            'users': User.objects.none()}
