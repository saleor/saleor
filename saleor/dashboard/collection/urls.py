from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.collection_list, name='collection-list'),
    url(r'^add/$', views.collection_create, name='collection-add'),
    url(r'^(?P<pk>[0-9]+)/edit/$',
        views.collection_update, name='collection-update'),
    url(r'^(?P<pk>[0-9]+)/publish/$', views.collection_toggle_is_published,
        name='collection-publish'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.collection_delete, name='collection-delete')]
