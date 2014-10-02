from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$',
        views.ProductListView.as_view(), name='products'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.ProductView.as_view(), name='product-update'),
    url(r'^add/(?P<category>[-\w]+)$',
        views.ProductView.as_view(), name='product-add'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.ProductDeleteView.as_view(), name='product-delete'),)
