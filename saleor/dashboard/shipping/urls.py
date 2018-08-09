from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.shipping_zone_list, name='shipping-zones'),
    url(r'^add/$', views.shipping_zone_add, name='shipping-zone-add'),
    url(r'^(?P<pk>\d+)/update/$', views.shipping_zone_edit,
        name='shipping-zone-update'),
    url(r'^(?P<pk>\d+)/$', views.shipping_zone_details,
        name='shipping-zone-details'),
    url(r'^(?P<pk>\d+)/delete/$',
        views.shipping_zone_delete, name='shipping-zone-delete'),

    url(r'^(?P<shipping_zone_pk>\d+)/shipping_method/add/$',
        views.shipping_method_add, name='shipping-method-add'),
    url(r'^(?P<shipping_zone_pk>\d+)/shipping_method/(?P<shipping_method_pk>\d+)/update/$',
        views.shipping_method_edit, name='shipping-method-edit'),
    url(r'^(?P<shipping_zone_pk>\d+)/shipping_method/(?P<shipping_method_pk>\d+)/delete/$',
        views.shipping_method_delete, name='shipping-method-delete')]
