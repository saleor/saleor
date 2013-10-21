from django.conf.urls import patterns, url, include

from . import views
from ..payment.urls import urlpatterns as payment_urls


TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')

urlpatterns = patterns(
    '',
    url(r'^%s/$' % TOKEN_PATTERN, views.details, name='details'),
    url(r'^%s/success/$' % TOKEN_PATTERN, views.success, name='success'),
    url(r'^%s/' % TOKEN_PATTERN, include(payment_urls, namespace='payment'))
)
