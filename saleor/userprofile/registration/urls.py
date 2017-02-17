from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^login/$', views.login, name="account_login"),
    url(r'^logout/$', views.logout, name="account_logout"),
    url(r'^signup/$', views.signup, name="account_signup"),
    url(r'^password/reset/$', views.login, name="account_reset_password"),
]
