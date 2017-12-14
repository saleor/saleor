from django.utils.translation import pgettext_lazy


class OrderStatus:
    NEW = 'new'
    CANCELLED = 'cancelled'
    SHIPPED = 'shipped'

    CHOICES = [
        (NEW, pgettext_lazy('order status', 'Processing')),
        (CANCELLED, pgettext_lazy('order status', 'Cancelled')),
        (SHIPPED, pgettext_lazy('order status', 'Shipped'))]
