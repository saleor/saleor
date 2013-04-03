from django.conf.urls import patterns, url


urlpatterns = patterns('payment.views',
    url(r'^payment/$', 'index', name='payment'),
    url(r'^authorizenet/$', 'authorizenet_payment', name='authorizenet'),
    url(r'^paypal/$', 'paypal_payment', name='paypal')
)
