from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.sale_list, name='sale-list'),
    url(r'(?P<pk>[0-9]+)/$', views.sale_edit, name='sale-update'),
    url(r'add/$', views.sale_edit, name='sale-add'),
    url(r'(?P<pk>[0-9]+)/delete/$', views.sale_delete, name='sale-delete'),
]
