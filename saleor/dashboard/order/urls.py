from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.order_list, name='orders'),
    url(r'^(?P<order_pk>\d+)/$',
        views.order_details, name='order-details'),
    url(r'^(?P<order_pk>\d+)/add-note/$',
        views.order_add_note, name='order-add-note'),
    url(r'^(?P<order_pk>\d+)/cancel/$',
        views.cancel_order, name='order-cancel'),
    url(r'^(?P<order_pk>\d+)/address/(?P<address_type>billing|shipping)/$',
        views.address_view, name='address-edit'),

    url(r'^(?P<order_pk>\d+)/payment/(?P<payment_pk>\d+)/capture/$',
        views.capture_payment, name='capture-payment'),
    url(r'^(?P<order_pk>\d+)/payment/(?P<payment_pk>\d+)/release/$',
        views.release_payment, name='release-payment'),
    url(r'^(?P<order_pk>\d+)/payment/(?P<payment_pk>\d+)/refund/$',
        views.refund_payment, name='refund-payment'),

    url(r'^(?P<order_pk>\d+)/line/(?P<line_pk>\d+)/change/$',
        views.orderline_change_quantity, name='orderline-change-quantity'),
    url(r'^(?P<order_pk>\d+)/line/(?P<line_pk>\d+)/split/$',
        views.orderline_split, name='orderline-split'),
    url(r'^(?P<order_pk>\d+)/line/(?P<line_pk>\d+)/cancel/$',
        views.orderline_cancel, name='orderline-cancel'),
    url(r'^(?P<order_pk>\d+)/line/(?P<line_pk>\d+)/change-stock/$',
        views.orderline_change_stock, name='orderline-change-stock'),
    url(r'^(?P<order_pk>\d+)/remove-voucher/$',
        views.remove_order_voucher, name='order-remove-voucher'),
    url(r'^(?P<order_pk>\d+)/shipment/(?P<group_pk>\d+)/ship/$',
        views.ship_delivery_group, name='ship-delivery-group'),
    url(r'^(?P<order_pk>\d+)/shipment/(?P<group_pk>\d+)/cancel/$',
        views.cancel_delivery_group, name='cancel-delivery-group'),
    url(r'^(?P<order_pk>\d+)/shipment/(?P<group_pk>\d+)/add-variant/$',
        views.add_variant_to_group, name='add-variant-to-group'),
    url(r'^(?P<order_pk>\d+)/invoice/$',
        views.order_invoice, name='order-invoice'),
    url(r'^(?P<group_pk>\d+)/packing-slips/$',
        views.order_packing_slip, name='order-packing-slips')]
