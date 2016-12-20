from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.details, name='details'),
    url(r'^address/(?P<pk>\d+)/delete/$',
        views.address_delete, name='address-delete'),
]
