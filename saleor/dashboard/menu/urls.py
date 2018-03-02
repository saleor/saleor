from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.menu_list, name='menu-list'),
    url(r'^add/$',
        views.menu_create, name='menu-add'),
    url(r'^(?P<pk>[0-9]+)/edit/$',
        views.menu_edit, name='menu-edit'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.menu_detail, name='menu-detail')]
