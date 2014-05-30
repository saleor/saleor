from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^orders/$', views.orders, name='orders'),
    url(r'^orders/(?P<pk>\d+)$', views.order_details, name='order-details'),
)
