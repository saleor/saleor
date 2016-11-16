from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'saleor-feed/$', views.saleor_feed, name='saleor-feed'),
]
