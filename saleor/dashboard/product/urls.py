from django.conf.urls import patterns, url

from . import api
from . import views


urlpatterns = patterns(
    '',
    url(r'^$',
        views.product_list, name='products'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.product_details, name='product-update'),
    url(r'^add/(?P<cls_name>[-\w]+)/$',
        views.product_details, name='product-add'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.ProductDeleteView.as_view(), name='product-delete'),

    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/$',
        views.product_image_edit, name='product-image-update'),
    url(r'^(?P<product_pk>[0-9]+)/images/add/$',
        views.product_image_edit, name='product-image-add'),
    url(r'^(?P<product_pk>[0-9]+)/images/(?P<img_pk>[0-9]+)/delete/$',
        views.product_image_delete, name='product-image-delete'),

    url('^(?P<product_pk>[0-9]+)/images/reorder/$',
        api.reorder_product_images, name='product-images-reorder'))
