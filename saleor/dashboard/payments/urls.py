from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.PaymentList.as_view(), name='payments'),
    url(r'^(?P<pk>[0-9]+)/$', views.payment_details, name='payment-details')
]
