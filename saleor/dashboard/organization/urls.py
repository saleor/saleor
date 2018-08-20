from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.organization_list, name='organizations'),
    url(r'^create/$', views.organization_create, name='organization-create'),
    url(r'^(?P<pk>[0-9]+)/$', views.organization_details, name='organization-details'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.organization_edit,
        name='organization-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.organization_delete,
        name='organization-delete'),
    url(r'^ajax/organizations/$', views.ajax_organizations_list,
        name='ajax-organizations-list')]
