from django.conf.urls import patterns, url

from . import views


urlpatterns = [
    url(r'^get_orders/$', views.get_orders_webhook, name='get_orders'),
    url(r'^get_products/$', views.get_products_webhook, name='get_products')
]

