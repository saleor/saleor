from django.conf.urls import patterns, url

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home')
]
