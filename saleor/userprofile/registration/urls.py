from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^login/$', views.login, name="account_login"),
    url(r'^logout', views.logout, name="account_logout"),
]
