from django.conf.urls import patterns, url

from . import views


urlpatterns = [
    url(r'^orders/$', views.OrderList.as_view(), name='order_list'),
    url(r'^products/$', views.ProductList.as_view(), name='product_list')
]

