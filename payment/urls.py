from django.conf.urls import patterns, url


urlpatterns = patterns('payment.views',
    url(r'^payment/$', 'index', name='index'),
    url(r'^remove/$', 'delete', name='delete'),
    url(r'^(?P<variant>[a-z-]+)/$', 'details', name='details')
)
