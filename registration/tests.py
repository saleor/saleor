from django.test.client import Client
from httpretty import HTTPretty, httprettified
from purl import URL


from django.test import TestCase


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/account/login/')

    def test_facebook_url(self):
        facebook_login_url = URL(
            self.response.context_data['facebook_login_url'])
        facebook_params = facebook_login_url.query_params()
        callback_url = URL(facebook_params['redirect_uri'][0])
        self.assertEqual(
            callback_url.path(),
            '/account/oauth_callback/facebook/')
        self.assertEqual(facebook_params['scope'], ['email'])
        self.assertEqual(facebook_params['client_id'],
                         ['YOUR_FACEBOOK_APP_ID'])
        self.assertNotIn('YOUR_FACEBOOK_APP_SECRET',
                         self.response.context_data['facebook_login_url'])

    def test_google_url(self):
        google_login_url = URL(self.response.context_data['google_login_url'])
        google_params = google_login_url.query_params()
        callback_url = URL(google_params['redirect_uri'][0])
        self.assertEqual(
            callback_url.path(),
            '/account/oauth_callback/google/')
        self.assertEqual(1, len(google_params['scope']))
        self.assertIn('https://www.googleapis.com/auth/userinfo.email',
                      google_params['scope'][0])
        self.assertIn('https://www.googleapis.com/auth/plus.me',
                      google_params['scope'][0])
        self.assertEqual(google_params['client_id'], ['YOUR_GOOGLE_APP_ID'])
        self.assertNotIn('YOUR_GOOGLE_APP_SECRET',
                         self.response.context_data['google_login_url'])


class CallbackViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.response = self.client.get('/account/login/')

    @httprettified
    def test_google_success(self):
        HTTPretty.register_uri(
            HTTPretty.POST, 'https://accounts.google.com/o/oauth2/token',
            body='{"access_token" : "dummy_token_content"}'
        )

        HTTPretty.register_uri(
            HTTPretty.GET,
            'https://www.googleapis.com/oauth2/v1/userinfo',
            body=('{"id": "fake_google_id","email": "fake@gmail.com",'
                  '"verified_email": true}'))

        response = self.client.get(
            '/account/oauth_callback/google/?code=dummycode')

        self.assertEqual(302, response.status_code)

        self.assertEqual('google',
                         self.client.session.get('external_service'))
        self.assertEqual('fake_google_id',
                         self.client.session.get('external_username'))
        self.assertEqual('fake@gmail.com',
                         self.client.session.get('confirmed_email'))

    @httprettified
    def test_google_bad_code(self):
        HTTPretty.register_uri(
            HTTPretty.POST, 'https://accounts.google.com/o/oauth2/token',
            body='{"error" : "some_error"}',
            status=400
        )

        response = self.client.get(
            '/account/oauth_callback/google/?code=wrongcode')

        self.assertEqual(302, response.status_code)

        self.assertEqual('/account/login/', URL(response['Location']).path())

    @httprettified
    def test_google_not_responding(self):
        HTTPretty.register_uri(
            HTTPretty.POST, 'https://accounts.google.com/o/oauth2/token',
            body='Some non-json data',
            status=500
        )

        response = self.client.get(
            '/account/oauth_callback/google/?code=wrongcode')

        self.assertEqual(302, response.status_code)

        self.assertEqual('/account/login/', URL(response['Location']).path())

    @httprettified
    def test_facebook_success(self):
        HTTPretty.register_uri(
            HTTPretty.GET, 'https://graph.facebook.com/oauth/access_token',
            body='access_token=dummy_token_content'
        )

        HTTPretty.register_uri(
            HTTPretty.GET,
            'https://graph.facebook.com/me',
            body=('{"id": "fake_facebook_id","email": "fake@facebook.com"}'))

        response = self.client.get(
            '/account/oauth_callback/facebook/?code=dummycode')

        self.assertEqual(302, response.status_code)

        self.assertEqual('facebook',
                         self.client.session.get('external_service'))
        self.assertEqual('fake_facebook_id',
                         self.client.session.get('external_username'))
        self.assertEqual('fake@facebook.com',
                         self.client.session.get('confirmed_email'))

    @httprettified
    def test_facebook_bad_code(self):
        HTTPretty.register_uri(
            HTTPretty.GET, 'https://graph.facebook.com/oauth/access_token',
            body='{"error": {"code": 100,'
                 '"message": "Invalid verification code format.",'
                 '"type": "OAuthException"}}',
            status=400
        )

        response = self.client.get(
            '/account/oauth_callback/facebook/?code=wrongcode')

        self.assertEqual(302, response.status_code)

        self.assertEqual('/account/login/', URL(response['Location']).path())

    @httprettified
    def test_facebook_not_responding(self):
        HTTPretty.register_uri(
            HTTPretty.POST, 'https://accounts.google.com/o/oauth2/token',
            body='Some data',
            status=500
        )

        response = self.client.get(
            '/account/oauth_callback/google/?code=wrongcode')

        self.assertEqual(302, response.status_code)

        self.assertEqual('/account/login/', URL(response['Location']).path())
