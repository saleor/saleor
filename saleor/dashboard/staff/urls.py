from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.staff_list, name='staff'),
    url(r'^(?P<pk>[0-9]+)/$', views.staff_details, name='staff-details')
]
