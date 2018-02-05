from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.staff_list, name='staff-list'),
    url(r'^staff-create/$', views.staff_create, name='staff-create'),
    url(r'^(?P<pk>[0-9]+)/$', views.staff_details, name='staff-details'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.staff_delete, name='staff-delete')]
