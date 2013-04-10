from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.loader import render_to_string

import facebook
import httplib2
import json
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError


def get_protocol_and_host(request):
    return 'http%(secure)s://%(host)s' % {
        'secure': 's' if request.is_secure() else '',
        'host': request.get_host()}


def get_callback_url(host, **kwargs):
    return host + reverse('registration:oauth_callback', kwargs=kwargs)


def get_google_flow(local_host, **kwargs):
    return OAuth2WebServerFlow(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_SECRET,
        redirect_uri=get_callback_url(host=local_host, service='google'),
        scope='https://www.googleapis.com/auth/plus.me '
              'https://www.googleapis.com/auth/userinfo.email',
        **kwargs)


def get_google_userinfo_url():
    return 'https://www.googleapis.com/oauth2/v1/userinfo'


def get_google_login_url(local_host):
    return ('https://accounts.google.com/o/oauth2/auth?'
            'scope=https://www.googleapis.com/auth/userinfo.email+'
            'https://www.googleapis.com/auth/plus.me'
            '&redirect_uri=%(callback)s'
            '&response_type=code'
            '&client_id=%(client_id)s' % {
                'callback': get_callback_url(host=local_host, service='google'),
                'client_id': settings.GOOGLE_CLIENT_ID
            })


def google_callback(local_host, data):
    code = data.get('code', '')
    try:
        credentials = get_google_flow(local_host).step2_exchange(code)
    except FlowExchangeError:  # TODO: log this
        return None, None
    http = credentials.authorize(httplib2.Http())
    # TODO: some smarter exception handling here
    try:
        _header, content = http.request(get_google_userinfo_url())
    except Exception:  # TODO: log this
        return None, None
    google_user_data = json.loads(content)
    external_username = google_user_data['id']
    if not google_user_data.get('verified_email'):
        return '', external_username
    return google_user_data['email'], external_username


def get_facebook_login_url(local_host):
    return facebook.auth_url(settings.FACEBOOK_APP_ID,
                             get_callback_url(host=local_host,
                                              service='facebook'),
                             ['email'])


def facebook_callback(local_host, data):
    code = data.get('code', '')
    try:
        facebook_auth_data = facebook.get_access_token_from_code(
            code, get_callback_url(host=local_host, service='facebook'),
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


def get_email_confirmation_message(local_host, email_confirmation):
    confirmation_url = local_host + reverse(
        'registration:confirm_email',
        kwargs={'pk': email_confirmation.pk,
                'token': email_confirmation.token})
    return render_to_string('registration/email/confirm_email_ownership.txt',
                            {'confirmation_url': confirmation_url})
