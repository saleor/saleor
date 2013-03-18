from django.template.loader import render_to_string
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.conf import settings

from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError
import facebook
import httplib2
import json


def get_callback_url(service):
    # TODO: domain
    return "http://localhost:8000" + reverse('registration:oauth_callback',
                                             kwargs={'service': service})


def get_google_flow(**kwargs):
    return OAuth2WebServerFlow(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_SECRET,
        redirect_uri=get_callback_url('google'),
        scope='https://www.googleapis.com/auth/plus.me '
              'https://www.googleapis.com/auth/userinfo.email',
        **kwargs)


def google_query_url():
    return ("https://www.googleapis.com/oauth2/v1/userinfo")


def get_google_login_url():
    return ('https://accounts.google.com/o/oauth2/auth?'
            'scope=https://www.googleapis.com/auth/userinfo.email+'
            'https://www.googleapis.com/auth/plus.me'
            '&redirect_uri=%(callback)s'
            '&response_type=code'
            '&client_id=%(client_id)s' % {
                'callback': get_callback_url('google'),
                'client_id': settings.GOOGLE_CLIENT_ID
            })


def google_callback(GET):
    code = GET.get('code', '')
    try:
        credentials = get_google_flow().step2_exchange(code)
    except FlowExchangeError:  # TODO: log this
        return None, None
    http = credentials.authorize(httplib2.Http())
    # TODO: some smarter exception handling here
    try:
        _header, content = http.request(google_query_url())
    except Exception:  # TODO: log this
        return None, None
    google_user_data = json.loads(content)
    email = (google_user_data['email']
             if google_user_data.get('verified_email')
             else '')
    external_username = google_user_data['id']

    return email, external_username


def get_facebook_login_url():
    return facebook.auth_url(settings.FACEBOOK_APP_ID,
                             get_callback_url('facebook'),
                             ['email'])


def facebook_callback(GET):
    try:
        facebook_auth_data = facebook.get_access_token_from_code(
            GET.get('code', ''), get_callback_url('facebook'),
            settings.FACEBOOK_APP_ID, settings.FACEBOOK_SECRET)
    except Exception:  # TODO: log this
        return None, None

    graph = facebook.GraphAPI(facebook_auth_data['access_token'])
    try:
        fb_user_data = graph.get_object('me')
    except Exception:  # TODO: log this
        return None, None

    external_username = fb_user_data.get('id')
    email = fb_user_data.get('email')

    return email, external_username


def get_email_confirmation_message(request, email_confirmation):
    return render_to_string(
        'registration/email/confirm_email_ownership.txt',
        {'confirmation_url':
            unicode(get_current_site(request))
            + reverse("registration:confirm_email", kwargs={
                'pk': email_confirmation.pk,
                'token': email_confirmation.token})})
