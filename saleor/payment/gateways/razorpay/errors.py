from django.utils.translation import pgettext_lazy

# Define the existing error messages as lazy `pgettext`.
ORDER_NOT_CHARGED = pgettext_lazy(
    'Razorpay payment error', 'Order was not charged.')
INVALID_REQUEST = pgettext_lazy(
    'Razorpay payment error', 'The payment data was invalid.')
SERVER_ERROR = pgettext_lazy(
    'Razorpay payment error', 'The order couldn\'t be proceeded.')
UNSUPPORTED_CURRENCY = pgettext_lazy(
    'Razorpay payment error', 'The %(currency)s currency is not supported.')
