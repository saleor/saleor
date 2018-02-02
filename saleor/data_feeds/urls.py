from django.conf.urls import url
from django.views.generic.base import RedirectView

from .google_merchant import get_feed_file_url

urlpatterns = [
    url(r'google/$',
        RedirectView.as_view(
            get_redirect_url=get_feed_file_url, permanent=True),
        name='google-feed')]
