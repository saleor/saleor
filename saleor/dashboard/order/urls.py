from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.OrderListView.as_view(),
        name='orders'),
    url(r'^(?P<pk>[0-9]+)$',
        views.OrderDetails.as_view(),
        name='order-details'),
    url(r'^(?P<order_pk>[0-9]+)/address/(?P<address_type>billing|shipping)$',
        views.AddressView.as_view(),
        name='address-edit'),
    url(r'^line/(?P<pk>[0-9]+)$',
        views.OrderLineEdit.as_view(),
        name='order-line-edit')
)
