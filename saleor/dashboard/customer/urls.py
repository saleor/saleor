from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.customer_list, name='customers'),
    url(r'^(?P<pk>[0-9]+)/$', views.customer_details, name='customer-details')
]
