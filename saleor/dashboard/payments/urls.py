from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.payment_list, name='payments'),
    url(r'^(?P<pk>[0-9]+)/$', views.payment_details, name='payment-details')
]
