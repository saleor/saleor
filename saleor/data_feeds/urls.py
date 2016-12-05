from django.conf.urls import url
from django.views.generic.base import RedirectView

from .google_merchant import FILE_URL

urlpatterns = [
    url(r'saleor-feed/$',
        RedirectView.as_view(url=FILE_URL), name='saleor-feed'),
]
