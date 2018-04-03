from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.homepage_block_list, name='homepage-blocks-list'),
    url(r'^add/$',
        views.homepage_block_create, name='homepage-blocks-add'),
    url(r'^(?P<pk>[0-9]+)/edit/$',
        views.homepage_block_edit, name='homepage-blocks-edit'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.homepage_block_delete, name='homepage-blocks-delete')]
