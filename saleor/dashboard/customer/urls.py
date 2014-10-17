from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.customer_list, name='customers'),
    url(r'^(?P<pk>[0-9]+)/$', views.customer_details, name='customer-details')
)
