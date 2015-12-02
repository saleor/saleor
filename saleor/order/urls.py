from django.conf.urls import url

from ..core import TOKEN_PATTERN
from . import views


urlpatterns = [
    url(r'^%s/$' % (TOKEN_PATTERN,), views.details, name='details'),
    url(r'^%s/payment/$' % (TOKEN_PATTERN,),
        views.payment, name='payment'),
    url(r'^%s/payment/(?P<variant>[-\w]+)/$' % (TOKEN_PATTERN,),
        views.start_payment, name='payment'),
    url(r'^%s/cancel-payment/$' % (TOKEN_PATTERN,), views.cancel_payment,
        name='cancel-payment')
]
