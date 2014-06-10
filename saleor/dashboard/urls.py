from django.conf.urls import patterns, url, include
from .views import dashboard

urlpatterns = patterns('', url('', include(dashboard.urls)))
