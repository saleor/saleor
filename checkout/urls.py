from django.conf.urls import patterns, url


urlpatterns = patterns('checkout.views',
    url(r'^$', 'details', kwargs={'step': None}, name='index'),
    url(r'^(?P<step>[a-z0-9-]+)/$', 'details', name='details')
)

