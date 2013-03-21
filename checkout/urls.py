from django.conf.urls import patterns, url


urlpatterns = patterns('checkout.views',
    url(r'^$', 'index', name='index'),
    url(r'^(?P<step>[a-z0-9-]+)/$', 'details', name='details')
)

