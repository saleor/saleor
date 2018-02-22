from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.page_list, name='page-list'),
    url(r'^add/$', views.page_add, name='page-add'),
    url(r'^(?P<pk>[0-9]+)/detail/$', views.page_detail, name='page-detail'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.page_edit, name='page-edit'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.page_delete, name='page-delete')]
