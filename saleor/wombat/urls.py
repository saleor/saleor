from django.conf.urls import patterns, url

from . import views


urlpatterns = [
    url(r'^get_orders/$', views.get_orders_webhook, name='get_orders'),
    url(r'^get_products/$', views.get_products_webhook, name='get_products'),
    url(r'^add_product/$', views.add_product_webhook, name='add_product'),
    url(r'^update_product/$', views.update_product_webhook, name='update_product'),
    url(r'^get_inventory/$', views.get_inventory_webhook, name='get_inventory')
]

