from django.conf.urls import patterns, url

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

    url(r'^categories/$',
        views.category_list, name='category-list'),
    url(r'^categories/(?P<pk>[0-9]+)/update/$',
        views.category_details, name='category-update'),
    url(r'^categories/add/$',
        views.category_details, name='category-add'))
