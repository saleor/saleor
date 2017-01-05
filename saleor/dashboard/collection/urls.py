from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.collection_list, name='collection-list'),
]
