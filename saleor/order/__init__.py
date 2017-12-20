from django.utils.translation import pgettext_lazy


class OrderStatus:
    OPEN = 'open'
    CLOSED = 'closed'

    CHOICES = [
        (OPEN, pgettext_lazy('order status', 'Open')),
        (CLOSED, pgettext_lazy('order status', 'Closed'))]


class GroupStatus:
    NEW = 'new'
    CANCELLED = 'cancelled'
    SHIPPED = 'shipped'

    CHOICES = [
        (NEW, pgettext_lazy('group status', 'Processing')),
        (CANCELLED, pgettext_lazy('group status', 'Cancelled')),
        (SHIPPED, pgettext_lazy('group status', 'Shipped'))]
