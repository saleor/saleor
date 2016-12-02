from django.conf.urls import url
from django.views.generic.base import RedirectView

from .feeds import SaleorGoogleMerchant

urlpatterns = [
    url(r'saleor-feed/$', RedirectView.as_view(url=SaleorGoogleMerchant.file_url),
        name='saleor-feed'),
]
