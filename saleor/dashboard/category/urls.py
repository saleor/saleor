from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.category_list, name='category-list'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.category_detail, name='category-detail'),
    url(r'^add/$',
        views.category_create, name='category-add'),
    url(r'^(?P<root_pk>[0-9]+)/add/$',
        views.category_create, name='category-add'),
    url(r'^(?P<root_pk>[0-9]+)/edit/$',
        views.category_edit, name='category-edit'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.category_delete, name='category-delete')]
