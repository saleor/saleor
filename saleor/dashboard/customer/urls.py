from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.customer_list, name='customers'),
    url(r'^create/$', views.customer_create, name='customer-create'),
    url(r'^(?P<pk>[0-9]+)/$', views.customer_details, name='customer-details'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.customer_edit,
        name='customer-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.customer_delete,
        name='customer-delete'),
    url(r'^ajax/users/$', views.ajax_users_list, name='ajax-users-list'),
    url(r'^(?P<customer_pk>[0-9]+)/add-note/$',
        views.customer_add_note, name='customer-add-note')]
