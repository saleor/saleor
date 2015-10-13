from django.conf.urls import patterns, url

from . import views


urlpatterns = [
    url(r'^orders/$', views.OrderList.as_view(), name='order_list')
]

