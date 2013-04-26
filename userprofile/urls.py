from django.conf.urls import patterns, url


urlpatterns = patterns(
    '',
    url(r'^$', 'userprofile.views.details', name='details'),
    url(r'^orders/$', 'userprofile.views.orders', name='orders'),
    url(r'^address/create/$',
        'userprofile.views.address_create',
        name='address-create'),
    url(r'^address/(?P<slug>[\w-]+)-(?P<pk>\d+)/edit/$',
        'userprofile.views.address_edit',
        name='address-edit'),
    url(r'^address/(?P<slug>[\w-]+)-(?P<pk>\d+)/delete/$',
        'userprofile.views.address_delete',
        name='address-delete'),
    url(r'^address/(?P<pk>\d+)/make-default-for-'
        '(?P<purpose>billing|shipping)/$',
        'userprofile.views.address_make_default',
        name='address-make-default'))
