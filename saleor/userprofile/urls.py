from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.details, name='details'),
    url(r'^orders/$', views.orders, name='orders'),
    url(r'^address/create/$', views.address_create,
        name='address-create'),
    url(r'^address/(?P<pk>\d+)/edit/$', views.address_edit,
        name='address-edit'),
    url(r'^address/(?P<pk>\d+)/delete/$',
        views.address_delete, name='address-delete'),
    url(r'^address/(?P<pk>\d+)/make-default-for-'
        r'(?P<purpose>billing|shipping)/$', views.address_make_default,
        name='address-make-default')
]
