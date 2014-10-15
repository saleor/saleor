from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.OrderListView.as_view(),
        name='orders'),
    url(r'^(?P<pk>[0-9]+)$',
        views.OrderDetails.as_view(),
        name='order-details'),
    url(r'^(?P<order_pk>[0-9]+)/address-billing$',
        views.address_view,
        name='address-billing-edit'),
    url(r'^(?P<order_pk>[0-9]+)/address-shipping/(?P<group_pk>[0-9]+)$',
        views.address_view,
        name='address-shipping-edit'),
    url(r'^line/(?P<pk>[0-9]+)$',
        views.order_line_edit,
        name='order-line-edit'),
    url(r'^ship/(?P<pk>[0-9]+)$',
        views.ship_delivery_group_modal,
        name='ship-delivery-group')
)
