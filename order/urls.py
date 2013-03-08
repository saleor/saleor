from django.conf.urls import patterns, url


urlpatterns = patterns('order.views',
    url(r'^(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})?$',
        'index', name='index'),
    url(r'^(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})/(?P<step>[a-z0-9-]+)/$',
        'details', name='details')
)

