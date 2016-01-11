from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.discount_list, name='discount-list'),
    url(r'(?P<pk>[0-9]+)/$',
        views.discount_edit, name='discount-update'),
    url(r'add/$',
        views.discount_edit, name='discount-add'),
    url(r'(?P<pk>[0-9]+)/delete/$',
        views.discount_delete, name='discount-delete'),
]
