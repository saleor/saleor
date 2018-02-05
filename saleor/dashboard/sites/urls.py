from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='site-index'),
    url(r'^(?P<pk>\d+)/update/$', views.site_settings_edit,
        name='site-update'),
    url(r'^(?P<pk>\d+)/$', views.site_settings_detail,
        name='site-detail'),
    url(r'^(?P<pk>\d+)/delete/$', views.site_settings_edit,
        name='site-delete'),

    url(r'^(?P<site_settings_pk>\d+)/authorization_key/add/$',
        views.authorization_key_add, name='authorization-key-add'),
    url(r'^(?P<site_settings_pk>\d+)/authorization_key/'
        r'(?P<key_pk>\d+)/update/$',
        views.authorization_key_edit, name='authorization-key-edit'),
    url(r'^(?P<site_settings_pk>\d+)/authorization_key/'
        r'(?P<key_pk>\d+)/delete/$',
        views.authorization_key_delete, name='authorization-key-delete')]
