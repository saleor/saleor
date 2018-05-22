from django.conf.urls import url

from . import views
from .views.discount import remove_voucher_view

urlpatterns = [
    url(r'^$', views.index_view, name='checkout-index'),
    url(r'^shipping-address/', views.shipping_address_view,
        name='checkout-shipping-address'),
    url(r'^shipping-method/', views.shipping_method_view,
        name='checkout-shipping-method'),
    url(r'^summary/', views.summary_view, name='checkout-summary'),
    url(r'^remove_voucher/', remove_voucher_view,
        name='checkout-remove-voucher'),
    url(r'^login/', views.login, name='checkout-login')]
