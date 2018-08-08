from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.shipping_method_list, name='shipping-methods'),
    url(r'^add/$', views.shipping_method_add, name='shipping-method-add'),
    url(r'^(?P<pk>\d+)/update/$', views.shipping_method_edit,
        name='shipping-method-update'),
    url(r'^(?P<pk>\d+)/$', views.shipping_method_details,
        name='shipping-method-details'),
    url(r'^(?P<pk>\d+)/delete/$',
        views.shipping_method_delete, name='shipping-method-delete'),

    url(r'^(?P<shipping_method_pk>\d+)/rate/add/$',
        views.shipping_rate_add, name='shipping-rate-add'),
    url(r'^(?P<shipping_method_pk>\d+)/rate/(?P<rate_pk>\d+)/update/$',
        views.shipping_rate_edit, name='shipping-rate-edit'),
    url(r'^(?P<shipping_method_pk>\d+)/rate/(?P<rate_pk>\d+)/delete/$',
        views.shipping_rate_delete, name='shipping-rate-delete')]
