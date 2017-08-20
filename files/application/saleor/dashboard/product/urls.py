from django.conf.urls import url

from . import api
from . import views


urlpatterns = [
    url(r'^$',
        views.product_list, name='product-list'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.product_edit, name='product-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.product_delete, name='product-delete'),
    url(r'^add/(?P<class_pk>[0-9]+)/$',
        views.product_create, name='product-add'),

    url(r'^classes/$',
        views.product_class_list, name='product-class-list'),
    url(r'^classes/add/$',
        views.product_class_create, name='product-class-add'),
    url(r'^classes/(?P<pk>[0-9]+)/update/$',
        views.product_class_edit, name='product-class-update'),
    url(r'^classes/(?P<pk>[0-9]+)/delete/$',
        views.product_class_delete, name='product-class-delete'),

    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/$',
        views.variant_edit, name='variant-update'),
    url(r'^(?P<product_pk>[0-9]+)/variants/add/$',
        views.variant_edit, name='variant-add'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/delete/$',
        views.variant_delete, name='variant-delete'),
    url(r'^(?P<product_pk>[0-9]+)/variants/bulk_delete/',
        views.variants_bulk_delete, name='variant-bulk-delete'),

    url(r'^(?P<product_pk>[0-9]+)/stock/(?P<stock_pk>[0-9]+)/$',
        views.stock_edit, name='product-stock-update'),
    url(r'^(?P<product_pk>[0-9]+)/stock/add/$',
        views.stock_edit, name='product-stock-add'),
    url(r'^(?P<product_pk>[0-9]+)/stock/(?P<stock_pk>[0-9]+)/delete/$',
        views.stock_delete, name='product-stock-delete'),
    url(r'^(?P<product_pk>[0-9]+)/stock/bulk_delete/',
        views.stock_bulk_delete, name='stock-bulk-delete'),

    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/$',
        views.product_image_edit, name='product-image-update'),
    url(r'^(?P<product_pk>[0-9]+)/images/add/$',
        views.product_image_edit, name='product-image-add'),
    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/delete/$',
        views.product_image_delete, name='product-image-delete'),
    url('^(?P<product_pk>[0-9]+)/images/reorder/$',
        api.reorder_product_images, name='product-images-reorder'),
    url('^(?P<product_pk>[0-9]+)/images/upload/$',
        api.upload_image, name='product-images-upload'),

    url(r'attributes/$',
        views.attribute_list, name='product-attributes'),
    url(r'attributes/(?P<pk>[0-9]+)/$',
        views.attribute_edit, name='product-attribute-update'),
    url(r'attributes/add/$',
        views.attribute_edit, name='product-attribute-add'),
    url(r'attributes/(?P<pk>[0-9]+)/delete/$',
        views.attribute_delete, name='product-attribute-delete'),

    url(r'stocklocations/$', views.stock_location_list,
        name='product-stock-location-list'),
    url(r'stocklocations/add/$', views.stock_location_edit,
        name='product-stock-location-add'),
    url(r'stocklocations/(?P<location_pk>[0-9]+)/$', views.stock_location_edit,
        name='product-stock-location-edit'),
    url(r'stocklocations/(?P<location_pk>[0-9]+)/delete/$',
        views.stock_location_delete, name='product-stock-location-delete'),
]
