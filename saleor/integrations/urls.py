from django.conf.urls import url
from django.views.generic.base import RedirectView

from .feeds import SaleorFeed

urlpatterns = [
    url(r'saleor-feed/$', RedirectView.as_view(url=SaleorFeed.file_url),
        name='saleor-feed'),
]
