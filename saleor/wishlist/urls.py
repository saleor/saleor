from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.user_wishlist, name='user-wishlist'),
    url(r'^public/(?P<token>[a-z0-9-]+?)/$',
        views.public_wishlist, name='public-wishlist'),
    url(r'^item/add/$', views.add_wishlist_item, name='add-item'),
    url(r'^item/(?P<item_pk>\d+?)/delete/$',
        views.delete_wishlist_item, name='item-delete')
]
