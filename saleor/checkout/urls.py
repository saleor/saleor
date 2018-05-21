from django.conf.urls import url

from . import views
from ..cart.checkout.views import shipping_address_view, shipping_method_view

urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^shipping-address/', shipping_address_view,
        name='shipping-address'),
    url(r'^shipping-method/', shipping_method_view,
        name='shipping-method'),
    url(r'^summary/', views.summary_view, name='summary'),
    url(r'^remove_voucher/', views.discount.remove_voucher_view,
        name='remove-voucher'),
    url(r'^login/', views.login, name='login')]
