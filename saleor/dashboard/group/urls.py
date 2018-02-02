from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.group_list, name='group-list'),
    url(r'^group-create/$', views.group_create, name='group-create'),
    url(r'^(?P<pk>[0-9]+)/$', views.group_details, name='group-details'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.group_delete, name='group-delete')]
