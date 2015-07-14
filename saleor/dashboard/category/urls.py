from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.category_root_nodes_list, name='category-root-list'),
    url(r'^(?P<root_pk>[0-9]+)/$',
        views.category_children_nodes_list, name='category-children-list'),
    url(r'^add/$',
        views.category_create, name='category-add'),
    url(r'^(?P<root_pk>[0-9]+)/add/$',
        views.category_create, name='category-add'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.category_delete, name='category-delete')
]
