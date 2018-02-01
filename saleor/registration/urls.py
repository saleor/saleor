from django.conf.urls import url
from django.contrib.auth import views as django_views

from . import views

urlpatterns = [
    url(r'^login/$', views.login, name='account_login'),
    url(r'^logout/$', views.logout, name='account_logout'),
    url(r'^signup/$', views.signup, name='account_signup'),
    url(r'^password/reset/$', views.password_reset,
        name='account_reset_password'),
    url(r'^password/reset/done/$', django_views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html'),
        name='account_reset_password_done'),
    url(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  # noqa
        views.password_reset_confirm, name='account_reset_password_confirm'),
    url(r'password/reset/complete/$', django_views.PasswordResetCompleteView.as_view(  # noqa
        template_name='account/password_reset_from_key_done.html'),
        name='account_reset_password_complete'),
]
