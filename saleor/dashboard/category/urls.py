from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(r'^$',
        views.category_list, name='categories'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.category_list, name='categories'),
    url(r'^add/$',
        views.category_details, name='category-add'),
    url(r'^(?P<pk>[0-9]+)/update/$',
        views.category_details, name='category-update'),
    url(r'^(?P<pk>[0-9]+)/delete/$',
        views.CategoryDeleteView.as_view(), name='category-delete'))
