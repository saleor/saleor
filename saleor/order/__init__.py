from django.utils.translation import pgettext_lazy


class OrderStatus:
    NEW = 'new'
    CANCELLED = 'cancelled'
    SHIPPED = 'shipped'
    PAYMENT_PENDING = 'payment-pending'
    FULLY_PAID = 'fully-paid'

    CHOICES = [
        (NEW, pgettext_lazy('order status', 'Processing')),
        (CANCELLED, pgettext_lazy('order status', 'Cancelled')),
        (SHIPPED, pgettext_lazy('order status', 'Shipped')),
        (PAYMENT_PENDING, pgettext_lazy('order status', 'Payment pending')),
        (FULLY_PAID, pgettext_lazy('order status', 'Fully paid'))]


class PaymentStatus:
    WAITING = 'waiting'
    PREAUTH = 'preauth'
    CONFIRMED = 'confirmed'
    REJECTED = 'rejected'
    REFUNDED = 'refunded'
    ERROR = 'error'
    INPUT = 'input'

    CHOICES = [
        (WAITING, pgettext_lazy('payment status', 'Waiting for confirmation')),
        (PREAUTH, pgettext_lazy('payment status', 'Pre-authorized')),
        (CONFIRMED, pgettext_lazy('payment status', 'Confirmed')),
        (REJECTED, pgettext_lazy('payment status', 'Rejected')),
        (REFUNDED, pgettext_lazy('payment status', 'Refunded')),
        (ERROR, pgettext_lazy('payment status', 'Error')),
        (INPUT, pgettext_lazy('payment status', 'Input'))]
