from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.customer_list, name='customers'),
    url(r'^create/$', views.customer_create, name='customer-create'),
    url(r'^(?P<pk>[0-9]+)/$', views.customer_details, name='customer-details'),
    url(r'^(?P<pk>[0-9]+)/update/$', views.customer_edit,
        name='customer-update')]
