from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.product_list, name='product-list'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.product_detail, name='product-detail'),
    url(r'^(?P<pk>[0-9]+)/publish/$', views.product_toggle_is_published,
        name='product-publish'),
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

    url(r'^(?P<product_pk>[0-9]+)/variants/add/$',
        views.variant_edit, name='variant-add'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/$',
        views.variant_details, name='variant-details'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/update/$',
        views.variant_edit, name='variant-update'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/delete/$',
        views.variant_delete, name='variant-delete'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/images/$',
        views.variant_images, name='variant-images'),

    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/stock/add/$',
        views.stock_edit, name='variant-stock-add'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/stock/'
        r'(?P<stock_pk>[0-9]+)/$',
        views.stock_details, name='variant-stock-details'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/stock/'
        r'(?P<stock_pk>[0-9]+)/update/$',
        views.stock_edit, name='variant-stock-update'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/stock/'
        r'(?P<stock_pk>[0-9]+)/delete/$',
        views.stock_delete, name='variant-stock-delete'),

    url(r'^(?P<product_pk>[0-9]+)/images/$', views.product_images,
        name='product-image-list'),
    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/$',
        views.product_image_edit, name='product-image-update'),
    url(r'^(?P<product_pk>[0-9]+)/images/add/$',
        views.product_image_edit, name='product-image-add'),
    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/delete/$',
        views.product_image_delete, name='product-image-delete'),

    url(r'^(?P<product_pk>[0-9]+)/images/reorder/$',
        views.ajax_reorder_product_images, name='product-images-reorder'),
    url(r'^(?P<product_pk>[0-9]+)/images/upload/$',
        views.ajax_upload_image, name='product-images-upload'),

    url(r'attributes/$',
        views.attribute_list, name='product-attributes'),
    url(r'attributes/(?P<pk>[0-9]+)/$',
        views.attribute_detail, name='product-attribute-detail'),
    url(r'attributes/(?P<pk>[0-9]+)/update/$',
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
