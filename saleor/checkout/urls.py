from django.conf.urls import patterns, url

from . import views


urlpatterns = [
    url(r'^$', views.details, kwargs={'step': None}, name='index'),
    url(r'^(?P<step>[a-z0-9-]+)/$', views.details, name='details')
]
