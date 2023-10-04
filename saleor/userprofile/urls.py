from django.urls import re_path

from . import views


urlpatterns = [
    re_path(r'^$', views.details, name='details'),
    re_path(r'^address/(?P<pk>\d+)/edit/$', views.address_edit,
        name='address-edit'),
    re_path(r'^address/(?P<pk>\d+)/delete/$',
        views.address_delete, name='address-delete'),
]
