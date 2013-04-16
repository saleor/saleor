from django.contrib.auth import get_user_model
from django.core.urlresolvers import resolve
from django.test import TestCase

from mock import Mock, MagicMock, patch, sentinel
from purl import URL

from .utils import (
    FACEBOOK,
    FacebookClient,
    GOOGLE,
    GoogleClient,
    OAuth2RequestAuthorizer,
    OAuth2Client,
    parse_response)
from .views import oauth_callback

User = get_user_model()

JSON_MIME_TYPE = 'application/json; charset=UTF-8'
URLENCODED_MIME_TYPE = 'application/x-www-form-urlencoded; charset=UTF-8'


class LoginUrlsTestCase(TestCase):
    """Tests login url generation."""

    def test_facebook_login_url(self):
        facebook_client = FacebookClient(local_host='localhost')
        facebook_login_url = URL(facebook_client.get_login_uri())
        query = facebook_login_url.query_params()
        callback_url = URL(query['redirect_uri'][0])
        func, args, kwargs = resolve(callback_url.path())
        self.assertEquals(func, oauth_callback)
        self.assertEquals(kwargs['service'], FACEBOOK)
        self.assertEqual(query['scope'][0], FacebookClient.scope)
        self.assertEqual(query['client_id'][0], FacebookClient.client_id)

    def test_google_login_url(self):
        google_client = GoogleClient(local_host='local_host')
        google_login_url = URL(google_client.get_login_uri())
        params = google_login_url.query_params()
        callback_url = URL(params['redirect_uri'][0])
        func, args, kwargs = resolve(callback_url.path())
        self.assertEquals(func, oauth_callback)
        self.assertEquals(kwargs['service'], GOOGLE)
        self.assertIn(params['scope'][0], GoogleClient.scope)
        self.assertEqual(params['client_id'][0], GoogleClient.client_id)


class ResponseParsingTestCase(TestCase):

    def setUp(self):
        self.response = MagicMock()

    def test_parse_json(self):
        self.response.headers = {'Content-Type': JSON_MIME_TYPE}
        self.response.json.return_value = sentinel.json_content
        content = parse_response(self.response)
        self.assertEquals(content, sentinel.json_content)

    def test_parse_urlencoded(self):
        self.response.headers = {'Content-Type': URLENCODED_MIME_TYPE}
        self.response.text = 'key=value&multi=a&multi=b'
        content = parse_response(self.response)
        self.assertEquals(content, {'key': 'value', 'multi': ['a', 'b']})


class TestClient(OAuth2Client):

    service = sentinel.service

    client_id = sentinel.client_id
    client_secret = sentinel.client_secret

    auth_uri = sentinel.auth_uri
    token_uri = sentinel.token_uri
    user_info_uri = sentinel.user_info_uri

    scope = sentinel.scope

    def get_redirect_uri(self):
        return sentinel.redirect_uri

    def extract_error_from_response(self, response_content):
        return 'some error'


class BaseCommunicationTestCase(TestCase):

    def setUp(self):
        self.parse_mock = patch('registration.utils.parse_response').start()

        self.requests_mock = patch('registration.utils.requests').start()
        self.requests_mock.codes.ok = sentinel.ok

        self.client = TestClient(local_host='http://localhost')

    def tearDown(self):
        patch.stopall()


class AccessTokenTestCase(BaseCommunicationTestCase):
    """Tests obtaining access_token."""

    def setUp(self):
        super(AccessTokenTestCase, self).setUp()

        self.parse_mock.return_value = {'access_token': sentinel.access_token}

        self.access_token_response = MagicMock()
        self.requests_mock.post.return_value = self.access_token_response

    def test_token_success(self):
        self.access_token_response.status_code = sentinel.ok
        access_token = self.client.get_access_token(code=sentinel.code)
        self.assertEquals(access_token, sentinel.access_token)
        self.requests_mock.post.assert_called_once_with(
            sentinel.token_uri,
            data={'grant_type': 'authorization_code',
                  'client_id': sentinel.client_id,
                  'client_secret': sentinel.client_secret,
                  'code': sentinel.code,
                  'redirect_uri': sentinel.redirect_uri,
                  'scope': sentinel.scope},
            auth=None)

    def test_token_failure(self):
        self.access_token_response.status_code = sentinel.fail
        self.assertRaises(ValueError, self.client.get_access_token,
                          code=sentinel.code)


class UserInfoTestCase(BaseCommunicationTestCase):
    """Tests obtaining user data."""

    def setUp(self):
        super(UserInfoTestCase, self).setUp()

        self.user_info_response = MagicMock()
        self.requests_mock.get.return_value = self.user_info_response

    def test_user_data_success(self):
        self.parse_mock.return_value = sentinel.user_info
        self.user_info_response.status_code = sentinel.ok
        user_info = self.client.get_user_info()
        self.assertEquals(user_info, sentinel.user_info)

    def test_user_data_failure(self):
        self.assertRaises(ValueError, self.client.get_user_info)

    def test_google_user_data_email_not_verified(self):
        self.user_info_response.status_code = sentinel.ok
        self.parse_mock.return_value = {'verified_email': False}
        google_client = GoogleClient(local_host='http://localhost')
        self.assertRaises(ValueError, google_client.get_user_info)

    def test_facebook_user_data_account_not_verified(self):
        self.user_info_response.status_code = sentinel.ok
        self.parse_mock.return_value = {'verified': False}
        facebook_client = FacebookClient(local_host='http://localhost')
        self.assertRaises(ValueError, facebook_client.get_user_info)


class AuthorizerTestCase(TestCase):

    def test_authorizes(self):
        authorizer = OAuth2RequestAuthorizer(access_token='token')
        request = Mock(headers={})
        authorizer(request)
        self.assertEquals('Bearer token', request.headers['Authorization'])
