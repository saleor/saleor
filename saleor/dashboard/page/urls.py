from django.conf.urls import url

from . import api, views


urlpatterns = [
    url(r'^$', views.page_list, name='page-list'),
    url(r'^add/$', views.page_add, name='page-add'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.page_edit, name='page-edit'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.page_delete, name='page-delete'),

    url(r'^home/$', views.homepage_block_list, name='homepage-block-list'),
    url(r'^home/add/$', views.homepage_block_add, name='homepage-block-add'),
    url(r'^home/(?P<pk>[0-9]+)/edit/$', views.homepage_block_edit,
        name='homepage-block-edit'),
    url(r'^home/(?P<pk>[0-9]+)/delete/$', views.homepage_block_delete,
        name='homepage-block-delete'),
    url('^home/reorder/$',
        api.reorder_homepage_blocks, name='homepage-blocks-reorder'),
]
