from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^setcountry/$', views.set_country, name='set-country'),
]
