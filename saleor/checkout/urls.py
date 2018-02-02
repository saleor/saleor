from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index_view, name='index'),
    url(r'^shipping-address/', views.shipping_address_view,
        name='shipping-address'),
    url(r'^shipping-method/', views.shipping_method_view,
        name='shipping-method'),
    url(r'^summary/', views.summary_view, name='summary'),
    url(r'^remove_voucher/', views.discount.remove_voucher_view,
        name='remove-voucher'),
    url(r'^login/', views.login, name='login')]
