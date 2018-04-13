from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.page_list, name='page-list'),
    url(r'^add/$', views.page_add, name='page-add'),
    url(r'^(?P<pk>[0-9]+)/$', views.page_details, name='page-details'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.page_update, name='page-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.page_delete, name='page-delete')]
