from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='setting-index'),
    url(r'^add/$', views.create, name='setting-create'),
]
