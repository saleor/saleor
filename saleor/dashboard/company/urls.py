from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.company_list, name='companies'),
    url(r'^create/$', views.company_create, name='company-create'),
    url(r'^(?P<pk>[0-9]+)/$', views.company_details, name='company-details'),
    url(r'^(?P<pk>[0-9]+)/$', views.company_details, name='company-details'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.company_edit,
        name='company-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.company_delete,
        name='company-delete'),
    url(r'^ajax/companies/$', views.ajax_companies_list,
        name='ajax-companies-list')]
