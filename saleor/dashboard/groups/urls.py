from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.groups_list, name="groups-list"),
    url(r'^group-create/$', views.group_create, name="group-create"),

    url(r'^(?P<pk>[0-9]+)/$', views.groups_details, name='group-details'),
]
