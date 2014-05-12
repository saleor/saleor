from django.conf.urls import patterns, url

from . import views


TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')

urlpatterns = patterns(
    '',
    url(r'^%s/$' % TOKEN_PATTERN, views.details, name='details'),
    url(r'^%s/payment/(?P<variant>[a-z-]+)/$' % TOKEN_PATTERN,
        views.start_payment, name='payment'),
    url(r'^%s/cancel-payment/$' % TOKEN_PATTERN, views.cancel_payment,
        name='cancel-payment'))
