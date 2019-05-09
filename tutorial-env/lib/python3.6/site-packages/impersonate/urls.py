# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^stop/$',
        views.stop_impersonate,
        name='impersonate-stop'),
    url(r'^list/$',
        views.list_users,
        {'template': 'impersonate/list_users.html'},
        name='impersonate-list'),
    url(r'^search/$',
        views.search_users,
        {'template': 'impersonate/search_users.html'},
        name='impersonate-search'),
    url(r'^(?P<uid>.+)/$',
        views.impersonate,
        name='impersonate-start'),
]
