from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^/$', views.collection_list, name='collection-list'),
    url(r'^add/$', views.collection_create, name='collection-add'),
    url(r'^(?P<collection_pk>[0-9]+)/edit/$',
        views.collection_update, name='collection-update'),
]
