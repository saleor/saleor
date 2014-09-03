from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
                       url(r'^$', views.CustomerList.as_view(),
                           name='customers'),
                       url(r'^(?P<pk>[0-9]+)$',
                           views.CustomerDetails.as_view(),
                           name='customer-details')
)

