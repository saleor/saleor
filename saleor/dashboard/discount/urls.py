from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'sale/$', views.sale_list, name='sale-list'),
    url(r'sale/add/$', views.sale_add, name='sale-add'),
    url(r'sale/(?P<pk>[0-9]+)/$', views.sale_edit, name='sale-update'),
    url(r'sale/(?P<pk>[0-9]+)/delete/$', views.sale_delete,
        name='sale-delete'),

    url(r'voucher/$', views.voucher_list, name='voucher-list'),
    url(r'voucher/add/$', views.voucher_add, name='voucher-add'),
    url(r'voucher/(?P<pk>[0-9]+)/$', views.voucher_edit,
        name='voucher-update'),
    url(r'voucher/(?P<pk>[0-9]+)/delete/$', views.voucher_delete,
        name='voucher-delete')]
