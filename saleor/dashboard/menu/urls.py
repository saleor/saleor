from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.menu_list, name='menu-list'),
    url(r'^add/$',
        views.menu_create, name='menu-add')]
