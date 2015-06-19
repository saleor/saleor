from django.conf.urls import patterns, url

from . import api
from . import views


urlpatterns = patterns(
    '',
    url(r'^$',
        views.product_list, name='products'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.product_details, name='product-update'),
    url(r'^add/(?P<product_cls>[-\w]+)/$',
        views.product_details, name='product-add'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.ProductDeleteView.as_view(), name='product-delete'),

    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/$',
        views.variant_edit, name='variant-update'),
    url(r'^(?P<product_pk>[0-9]+)/variants/add/$',
        views.variant_edit, name='variant-add'),
    url(r'^(?P<product_pk>[0-9]+)/variants/(?P<variant_pk>[0-9]+)/delete/$',
        views.variant_delete, name='variant-delete'),

    url(r'^(?P<product_pk>[0-9]+)/stock/(?P<stock_pk>[0-9]+)/$',
        views.stock_edit, name='product-stock-update'),
    url(r'^(?P<product_pk>[0-9]+)/stock/add/$',
        views.stock_edit, name='product-stock-add'),
    url(r'^(?P<product_pk>[0-9]+)/stock/(?P<stock_pk>[0-9]+)/delete/$',
        views.stock_delete, name='product-stock-delete'),

    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/$',
        views.product_image_edit, name='product-image-update'),
    url(r'^(?P<product_pk>[0-9]+)/images/add/$',
        views.product_image_edit, name='product-image-add'),
    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/delete/$',
        views.product_image_delete, name='product-image-delete'),
    url('^(?P<product_pk>[0-9]+)/images/reorder/$',
        api.reorder_product_images, name='product-images-reorder'))
