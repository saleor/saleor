from django.conf.urls import patterns, url, include


urlpatterns = patterns('',
    url(r'^(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
        '-[0-9a-z]{12})/', include('payment.urls', namespace='payment'))
)
