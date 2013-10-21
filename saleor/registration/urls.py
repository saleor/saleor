from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^oauth_callback/(?P<service>\w+)/$', views.oauth_callback,
        name='oauth_callback'),
    url(r'^change_password/$', views.change_password,
        name='change_password'),
    url(r'^request_email_confirmation/$', views.request_email_confirmation,
        name='request_email_confirmation'),
    url(r'^confirm_email/(?P<token>\w+)/$', views.confirm_email,
        name='confirm_email'),
    url(r'^request_email_change/$', views.request_email_change,
        name='request_email_change'),
    url(r'^change_email/(?P<token>\w+)/$', views.change_email,
        name='change_email'))
