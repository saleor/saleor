from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.category_list, name='categories'),
    url(r'^(?P<root>[0-9]+)/$',
        views.category_list, name='categories'),
    url(r'^add/$',
        views.category_details, name='category-add'),
    url(r'^(?P<parent_pk>[0-9]+)/add/$',
        views.category_details, name='category-add'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.category_details, name='category-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.category_delete, name='category-delete')
]
