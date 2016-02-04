from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'sale/$', views.sale_list, name='sale-list'),
    url(r'sale/(?P<pk>[0-9]+)/$', views.sale_edit, name='sale-update'),
    url(r'sale/add/$', views.sale_edit, name='sale-add'),
    url(r'sale/(?P<pk>[0-9]+)/delete/$', views.sale_delete, name='sale-delete'),

    url(r'voucher/$', views.voucher_list, name='voucher-list'),
    url(r'voucher/(?P<pk>[0-9]+)/$', views.voucher_edit, name='voucher-update'),
    url(r'voucher/add/$', views.voucher_edit, name='voucher-add'),
    url(r'voucher/(?P<pk>[0-9]+)/delete/$', views.voucher_delete, name='voucher-delete'),
]
