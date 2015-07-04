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
    url(r'^line/(?P<pk>[0-9]+)/$', views.edit_order_line,
        name='order-line-edit'),
    url(r'^line/(?P<pk>[0-9]+)/(?P<action>change_quantity|move_items)/$',
        views.edit_order_line, name='order-line-edit'),
    url(r'^ship/(?P<pk>[0-9]+)/$', views.ship_delivery_group,
        name='ship-delivery-group')
]
