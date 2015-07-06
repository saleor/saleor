from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.category_list, name='category-list'),
    url(r'^(?P<root_pk>[0-9]+)/$',
        views.category_list, name='category-list'),
    url(r'^add/$',
        views.category_create, name='category-add'),
    url(r'^(?P<root_pk>[0-9]+)/add/$',
        views.category_create, name='category-add'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.category_edit, name='category-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.category_delete, name='category-delete')
]
