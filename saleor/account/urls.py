from django.conf.urls import url
from django.contrib.auth import views as django_views

from . import views

urlpatterns = [
    url(r'^$', views.details, name='details'),

    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^password/reset/$', views.password_reset,
        name='reset-password'),
    url(r'^password/reset/done/$', django_views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html'),
        name='reset-password-done'),
    url(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  # noqa
        views.password_reset_confirm, name='reset-password-confirm'),
    url(r'password/reset/complete/$', django_views.PasswordResetCompleteView.as_view(  # noqa
        template_name='account/password_reset_from_key_done.html'),
        name='reset-password-complete'),

    url(r'^address/(?P<pk>\d+)/edit/$', views.address_edit,
        name='address-edit'),
    url(r'^address/(?P<pk>\d+)/delete/$',
        views.address_delete, name='address-delete'),
    url(r'^account/(?P<token>[0-9A-Za-z_\-]+)/delete/$', views.account_delete,
        name='account-delete'),
    url(r'^account/(?P<token>[0-9A-Za-z_\-]+)/delete/',
        views.account_delete_confirm, name='account-delete-confirm')]
