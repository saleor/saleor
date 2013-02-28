from django.conf.urls import patterns, url


urlpatterns = patterns('order.views',
    url(r'^$', 'billing_address', name='billing-address'),
)

