from django.conf.urls import patterns, url, include

TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')

urlpatterns = patterns('order.views',
    url(r'^%s/success/$' % TOKEN_PATTERN, 'success', name='success'),
    url(r'^%s/' % TOKEN_PATTERN, include('payment.urls', namespace='payment'))
)
