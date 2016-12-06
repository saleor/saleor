from django.conf.urls import url
from django.views.generic.base import RedirectView

from .google_merchant import FILE_URL

urlpatterns = [
    url(r'google/$',
        RedirectView.as_view(url=FILE_URL), name='google-feed')]
