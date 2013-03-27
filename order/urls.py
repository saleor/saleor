from django.conf.urls import patterns, url


urlpatterns = patterns('order.views',
    url(r'^(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
        '-[0-9a-z]{12})/payment/$', 'payment', name='payment')
)

