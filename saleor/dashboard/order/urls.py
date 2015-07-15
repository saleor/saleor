from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.OrderListView.as_view(), name='orders'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.order_details, name='order-details'),
    url(r'^(?P<order_pk>[0-9]+)/address-(?P<address_type>billing|shipping)/$',
        views.address_view, name='address-edit'),
    url(r'^payment/(?P<pk>[0-9]+)/(?P<action>capture|refund|release)/$',
        views.manage_payment, name='manage-payment'),
    url(r'^line/change/(?P<pk>[0-9]+)/$', views.orderline_change_quantity,
        name='orderline-change-quantity'),
    url(r'^line/split/(?P<pk>[0-9]+)/$', views.orderline_split,
        name='orderline-split'),
    url(r'^ship/(?P<pk>[0-9]+)/$', views.ship_delivery_group,
        name='ship-delivery-group')
]
