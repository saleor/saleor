from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^style-guide/', views.styleguide, name='styleguide'),
    url(r'^impersonate-msg/(?P<uid>\d+)/', views.impersonate_with_msg,
        name='impersonate-msg'),
]
