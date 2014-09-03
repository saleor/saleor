from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
                       url(r'^$', views.OrderListView.as_view(),
                           name='orders'),
                       url(r'^(?P<pk>[0-9]+)$',
                           views.OrderDetails.as_view(),
                           name='order-details')
)
