from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^payment/$', views.index, name='index'),
    url(r'^remove/$', views.delete, name='delete'),
    url(r'^(?P<variant>[a-z-]+)/$', views.details, name='details')
)
