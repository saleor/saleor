from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
                       url(r'^$', views.PaymentList.as_view(),
                           name='payments'),
                       url(r'^(?P<pk>[0-9]+)/$',
                           views.PaymentDetails.as_view(),
                           name='payment-details')
)
