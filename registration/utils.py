from django.core.urlresolvers import reverse
from django.conf import settings

from oauth2client.client import OAuth2WebServerFlow


def callback_url(service):
    # TODO: domain
    return "http://localhost:8000" + reverse('registration:oauth_callback',
                                             kwargs={'service': service})


def get_google_flow(**kwargs):
    return OAuth2WebServerFlow(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_SECRET,
        redirect_uri=callback_url('google'),
        scope='https://www.googleapis.com/auth/plus.me '
              'https://www.googleapis.com/auth/userinfo.email',
        **kwargs)


def google_query_url():
    return ("https://www.googleapis.com/oauth2/v1/userinfo")
