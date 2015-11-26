from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^update/(?P<product_id>\d+)/$', views.index, name='update_line')
]
