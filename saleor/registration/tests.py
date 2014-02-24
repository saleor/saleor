from unittest import TestCase

from django.contrib.auth import get_user_model
from django.core.urlresolvers import resolve
from django.conf import settings
from mock import call, Mock, MagicMock, patch, sentinel
from purl import URL

from .forms import OAuth2CallbackForm
from .utils import (
    FACEBOOK,
    FacebookClient,
    GOOGLE,
    GoogleClient,
    OAuth2RequestAuthorizer,
    OAuth2Client,
    parse_response)
from .views import oauth_callback, change_email

User = get_user_model()

JSON_MIME_TYPE = 'application/json; charset=UTF-8'
URLENCODED_MIME_TYPE = 'application/x-www-form-urlencoded; charset=UTF-8'


class SessionMock(Mock):

    def __setitem__(self, key, value):
        pass


class LoginUrlsTestCase(TestCase):
    """Tests login url generation."""

    def test_facebook_login_url(self):
        """Facebook login url is properly generated"""
        facebook_client = FacebookClient(local_host='localhost')
        facebook_login_url = URL(facebook_client.get_login_uri())
        query = facebook_login_url.query_params()
        callback_url = URL(query['redirect_uri'][0])
        func, _args, kwargs = resolve(callback_url.path())
        self.assertEquals(func, oauth_callback)
        self.assertEquals(kwargs['service'], FACEBOOK)
        self.assertEqual(query['scope'][0], FacebookClient.scope)
        self.assertEqual(query['client_id'][0], str(FacebookClient.client_id))

    def test_google_login_url(self):
        """Google login url is properly generated"""
        google_client = GoogleClient(local_host='local_host')
        google_login_url = URL(google_client.get_login_uri())
        params = google_login_url.query_params()
        callback_url = URL(params['redirect_uri'][0])
        func, _args, kwargs = resolve(callback_url.path())
        self.assertEquals(func, oauth_callback)
        self.assertEquals(kwargs['service'], GOOGLE)
        self.assertTrue(params['scope'][0] in GoogleClient.scope)
        self.assertEqual(params['client_id'][0], str(GoogleClient.client_id))


class ResponseParsingTestCase(TestCase):

    def setUp(self):
        self.response = MagicMock()

    def test_parse_json(self):
        """OAuth2 client is able to parse json response"""
        self.response.headers = {'Content-Type': JSON_MIME_TYPE}
        self.response.json.return_value = sentinel.json_content
        content = parse_response(self.response)
        self.assertEquals(content, sentinel.json_content)

    def test_parse_urlencoded(self):
        """OAuth2 client is able to parse urlencoded response"""
        self.response.headers = {'Content-Type': URLENCODED_MIME_TYPE}
        self.response.text = 'key=value&multi=a&multi=b'
        content = parse_response(self.response)
        self.assertEquals(content, {'key': 'value', 'multi': ['a', 'b']})


class TestClient(OAuth2Client):
    """OAuth2Client configured for testing purposes."""

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
        self.parse_mock = patch(
            'saleor.registration.utils.parse_response').start()
        self.requests_mock = patch(
            'saleor.registration.utils.requests').start()
        self.requests_mock.codes.ok = sentinel.ok

    def tearDown(self):
        patch.stopall()


class AccessTokenTestCase(BaseCommunicationTestCase):
    """Tests obtaining access_token."""

    def setUp(self):
        super(AccessTokenTestCase, self).setUp()

        self.parse_mock.return_value = {'access_token': sentinel.access_token}

        self.access_token_response = MagicMock()
        self.requests_mock.post.return_value = self.access_token_response

    def test_token_is_obtained_on_construction(self):
        """OAuth2 client asks for access token if interim code is available"""
        self.access_token_response.status_code = sentinel.ok
        TestClient(local_host='http://localhost', code=sentinel.code)
        self.requests_mock.post.assert_called_once()

    def test_token_success(self):
        """OAuth2 client properly obtains access token"""
        client = TestClient(local_host='http://localhost')
        self.access_token_response.status_code = sentinel.ok
        access_token = client.get_access_token(code=sentinel.code)
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
        """OAuth2 client properly reacts to access token fetch failure"""
        client = TestClient(local_host='http://localhost')
        self.access_token_response.status_code = sentinel.fail
        self.assertRaises(ValueError, client.get_access_token,
                          code=sentinel.code)


class UserInfoTestCase(BaseCommunicationTestCase):
    """Tests obtaining user data."""

    def setUp(self):
        super(UserInfoTestCase, self).setUp()

        self.user_info_response = MagicMock()
        self.requests_mock.get.return_value = self.user_info_response

    def test_user_info_success(self):
        """OAuth2 client properly fetches user info"""
        client = TestClient(local_host='http://localhost')
        self.parse_mock.return_value = sentinel.user_info
        self.user_info_response.status_code = sentinel.ok
        user_info = client.get_user_info()
        self.assertEquals(user_info, sentinel.user_info)

    def test_user_data_failure(self):
        """OAuth2 client reacts well to user info fetch failure"""
        client = TestClient(local_host='http://localhost')
        self.assertRaises(ValueError, client.get_user_info)

    def test_google_user_data_email_not_verified(self):
        """Google OAuth2 client checks for email verification"""
        self.user_info_response.status_code = sentinel.ok
        self.parse_mock.return_value = {'verified_email': False}
        google_client = GoogleClient(local_host='http://localhost')
        self.assertRaises(ValueError, google_client.get_user_info)

    def test_facebook_user_data_account_not_verified(self):
        """Facebook OAuth2 client checks for account verification"""
        self.user_info_response.status_code = sentinel.ok
        self.parse_mock.return_value = {'verified': False}
        facebook_client = FacebookClient(local_host='http://localhost')
        self.assertRaises(ValueError, facebook_client.get_user_info)


class AuthorizerTestCase(TestCase):

    def test_authorizes(self):
        """OAuth2 authorizer sets proper auth headers"""
        authorizer = OAuth2RequestAuthorizer(access_token='token')
        request = Mock(headers={})
        authorizer(request)
        self.assertEquals('Bearer token', request.headers['Authorization'])


class CallbackTestCase(TestCase):

    def setUp(self):
        patcher = patch(
            'saleor.registration.forms.get_client_class_for_service')
        self.getter_mock = patcher.start()
        patcher = patch('saleor.registration.forms.authenticate')
        self.authenticate_mock = patcher.start()

        self.client_class = self.getter_mock()
        self.client = self.client_class()
        self.client.get_user_info.return_value = {'id': sentinel.id,
                                                  'email': sentinel.email}

        self.form = OAuth2CallbackForm(service=sentinel.service,
                                       local_host=sentinel.local_host,
                                       data={'code': 'test_code'})
        self.assertTrue(self.form.is_valid(), self.form.errors)

    @patch('saleor.registration.forms.ExternalUserData')
    @patch('saleor.registration.forms.User')
    def test_new_user(self, user_mock, external_data_mock):
        """OAuth2 callback creates a new user with proper external data"""
        user_mock.objects.get_or_create.return_value = sentinel.user, None
        self.authenticate_mock.side_effect = [None, sentinel.authed_user]

        user = self.form.get_authenticated_user()

        self.assertEquals(self.authenticate_mock.mock_calls,
                          [call(service=sentinel.service,
                                username=sentinel.id),
                           call(user=sentinel.user)])
        external_data_mock.objects.create.assert_called_once_with(
            service=sentinel.service, username=sentinel.id, user=sentinel.user)
        self.assertEquals(user, sentinel.authed_user)

    def test_existing_user(self):
        """OAuth2 recognizes existing user via external data credentials"""
        self.authenticate_mock.return_value = sentinel.authed_user

        user = self.form.get_authenticated_user()

        self.assertEquals(user, sentinel.authed_user)
        self.authenticate_mock.assert_called_once_with(
            service=sentinel.service, username=sentinel.id)

    def tearDown(self):
        patch.stopall()


class EmailChangeTestCase(TestCase):

    @patch('saleor.registration.views.now')
    @patch('saleor.registration.views.EmailChangeRequest.objects.get')
    def test_another_user_logged_out(self, get, now):

        # user requests email change
        user = Mock()
        token_object = Mock()
        token_object.token = 'sometokencontent'
        token_object.user = user
        get.return_value = token_object

        # another user is logged in
        another_user = Mock()
        request = Mock()
        request.user = another_user
        request.session = SessionMock()

        # first user clicks link in his email
        result = change_email(request, token_object.token)
        self.assertEquals(result.status_code, 302)
        get.assert_called_once_with(
            token=token_object.token, valid_until__gte=now())
        self.assertFalse(request.user.is_authenticated())
        token_object.delete.assert_not_called()

    @patch('saleor.registration.views.now')
    @patch('saleor.registration.views.EmailChangeRequest.objects.get')
    def test_user_logged_in(self, get, now):

        # user requests email change
        user = Mock()
        token_object = Mock()
        token_object.token = 'sometokencontent'
        token_object.user = user
        get.return_value = token_object

        # user is logged in
        request = Mock()
        request.user = user

        # user clicks link in his email
        result = change_email(request, token_object.token)
        self.assertEquals(result.status_code, 302)
        get.assert_called_once_with(
            token=token_object.token, valid_until__gte=now())
        # user stays logged in
        self.assertTrue(request.user.is_authenticated())
        # token is deleted
        token_object.delete.assert_called_once_with()
        user.save.assert_called_once_with()
        # user email gets changed
        self.assertEqual(user.email, token_object.email)


class OAuthClientTestCase(TestCase):
    def setUp(self):
        self.fake_client_id = 'test'
        self.fake_client_secret = 'testsecret'

    def test_google_secrets_override(self):
        client = GoogleClient(local_host='http://localhost',
                              client_id=self.fake_client_id,
                              client_secret=self.fake_client_secret)
        self.assertEqual(client.client_id, self.fake_client_id)
        self.assertEqual(client.client_secret, self.fake_client_secret)

    def test_google_secrets_fallback(self):
        client = GoogleClient(local_host='http://localhost')
        self.assertEqual(client.client_id, settings.GOOGLE_CLIENT_ID)
        self.assertEqual(client.client_secret, settings.GOOGLE_CLIENT_SECRET)

    def test_facebook_secrets_override(self):
        client = FacebookClient(local_host='http://localhost',
                                client_id=self.fake_client_id,
                                client_secret=self.fake_client_secret)
        self.assertEqual(client.client_id, self.fake_client_id)
        self.assertEqual(client.client_secret, self.fake_client_secret)

    def test_facebook_secrets_fallback(self):
        client = FacebookClient(local_host='http://localhost')
        self.assertEqual(client.client_id, settings.FACEBOOK_APP_ID)
        self.assertEqual(client.client_secret, settings.FACEBOOK_SECRET)
