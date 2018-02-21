from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<url>[a-z0-9-_]+?)/$',
        views.page_detail, name='details')]
