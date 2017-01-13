from django.conf.urls import url
from django.views.decorators.http import require_POST

from . import views

remove_voucher_view = require_POST(views.discount.remove_voucher_view)


urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^shipping-address/', views.shipping_address_view,
        name='shipping-address'),
    url(r'^shipping-method/', views.shipping_method_view,
        name='shipping-method'),
    url(r'^summary/', views.summary_view, name='summary'),
    url(r'^remove_voucher/', remove_voucher_view, name='remove-voucher'),
    url(r'^login/', views.login, name='login'),
]
