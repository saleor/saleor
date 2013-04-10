from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

import datetime
from httpretty import HTTPretty, httprettified
from purl import URL

from .models import EmailConfirmation, ExternalUserData

User = get_user_model()


class LoginViewTest(TestCase):

    def setUp(self):
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
    def test_google_success_second_time(self):
        user = User.objects.create(email='fake@email.com')
        ExternalUserData.objects.create(
            username='fake_google_id', provider='google', user=user)

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

        self.assertNotIn('confirmed_email', self.client.session)
        self.assertNotIn('external_username', self.client.session)
        self.assertNotIn('external_service', self.client.session)

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


class RegisterViewTest(TestCase):

    def test_registration_page(self):

        initial_user_count = User.objects.count()

        response = self.client.get('/account/register/')

        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.context_data['form'].is_valid())
        self.assertFalse(response.context_data['form'].errors)

    def test_register_new(self):

        initial_user_count = User.objects.count()
        email = 'some.non.exeistanst@email.com'
        self.assertFalse(User.objects.filter(email=email).exists())
        self.assertFalse(
            EmailConfirmation.objects.filter(email=email).exists())

        response = self.client.post('/account/register/', {'email': email})

        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(302, response.status_code)
        self.assertTrue(EmailConfirmation.objects.filter(email=email).exists())

    def test_send_reset_password_token(self):

        email = 'some@email.com'
        user, _ = User.objects.get_or_create(email=email)
        initial_user_count = User.objects.count()
        self.assertFalse(
            EmailConfirmation.objects.filter(email=email).exists())

        response = self.client.post('/account/register/', {'email': email})

        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(302, response.status_code)
        self.assertTrue(EmailConfirmation.objects.filter(email=email).exists())

    def test_register_with_extrnally_confirmed_email_and_no_extern_login(self):
        # if we don't impose some action for TestClient we shall not be able to
        # set variables to session
        self.client.get('/')

        email = 'some@email.com'
        self.assertFalse(User.objects.filter(email=email).exists())
        initial_user_count = User.objects.count()
        initial_email_confirmation_count = EmailConfirmation.objects.count()

        session = self.client.session
        session['confirmed_email'] = email
        session.save()

        response = self.client.post('/account/register/', {'email': email})

        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(
            initial_email_confirmation_count,
            EmailConfirmation.objects.count())
        self.assertEqual(400, response.status_code)
        self.assertFalse('confirmed_email' in self.client.session)

    def test_register_with_externally_confirmed_email(self):
        # if we don't impose some action for TestClient we shall not be able to
        # set variables to session
        self.client.get('/')

        email = 'some@email.com'

        self.assertFalse(User.objects.filter(email=email).exists())

        initial_user_count = User.objects.count()
        initial_email_confirmation_count = EmailConfirmation.objects.count()

        session = self.client.session
        session['confirmed_email'] = email
        session['external_username'] = 'some_external_id'
        session['external_service'] = 'a_service'
        session.save()

        response = self.client.post('/account/register/', {'email': email})

        self.assertEqual(initial_user_count + 1, User.objects.count())
        self.assertEqual(302, response.status_code)
        self.assertFalse(EmailConfirmation.objects.filter(email=email).exists())
        self.assertEqual(
            initial_email_confirmation_count,
            EmailConfirmation.objects.count())

    def test_register_from_external_provider_and_change_email(self):
        # if we don't impose some action for TestClient we shall not be able to
        # set variables to session
        self.client.get('/')

        initial_user_count = User.objects.count()
        confirmed_email = 'confirmed@email.com'
        supplied_email = 'supplied@email.com'
        self.assertFalse(User.objects.filter(email=supplied_email).exists())
        self.assertFalse(
            EmailConfirmation.objects.filter(email=supplied_email).exists())

        session = self.client.session
        session['confirmed_email'] = confirmed_email
        session['external_username'] = 'some_external_id'
        session['external_service'] = 'a_service'
        session.save()

        response = self.client.post(
            '/account/register/', {'email': supplied_email})

        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(302, response.status_code)
        self.assertTrue(EmailConfirmation.objects.filter(
            email=supplied_email).exists())


class ConfirmationEmailTest(TestCase):

    def test_confirm_new_email(self):
        email = 'email@example.com'
        self.assertFalse(User.objects.filter(email=email).exists())
        ec = EmailConfirmation.objects.create(email=email)
        initial_user_count = User.objects.count()

        response = self.client.get(
            '/account/confirm_email/%s/%s/' % (ec.id, ec.token))

        self.assertTrue(EmailConfirmation.objects.filter(pk=ec.pk).exists())
        self.assertFalse(User.objects.filter(email=email).exists())
        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(200, response.status_code)

    def test_confirm_new_email_and_set_password(self):
        email = 'email@example.com'
        password = 's0m3 P4sSw0rd'
        self.assertFalse(User.objects.filter(email=email).exists())
        initial_user_count = User.objects.count()

        ec = EmailConfirmation.objects.create(email=email)

        response = self.client.post(
            '/account/confirm_email/%s/%s/' % (ec.id, ec.token),
            {'new_password1': password,
             'new_password2': password})

        self.assertTrue(User.objects.get(email=email).check_password(password))
        self.assertFalse(EmailConfirmation.objects.filter(pk=ec.pk).exists())
        self.assertTrue(User.objects.get(email=email).is_active)
        self.assertEqual(initial_user_count + 1, User.objects.count())
        self.assertEqual(302, response.status_code)

    def test_confirm_new_email_and_dont_set_password(self):
        email = 'email@example.com'
        self.assertFalse(User.objects.filter(email=email).exists())
        initial_user_count = User.objects.count()

        ec = EmailConfirmation.objects.create(email=email)

        response = self.client.post(
            '/account/confirm_email/%s/%s/' % (ec.id, ec.token),
            {'no_password': True})

        user = User.objects.get(email=email)
        self.assertFalse(EmailConfirmation.objects.filter(pk=ec.pk).exists())
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_active)
        self.assertEqual(initial_user_count + 1, User.objects.count())
        self.assertEqual(302, response.status_code)

    def test_confirm_existing_email_and_set_password(self):
        email = 'email@example.com'
        password = 's0m3 P4sSw0rd'
        User.objects.create(email=email)

        initial_user_count = User.objects.count()

        ec = EmailConfirmation.objects.create(email=email)

        response = self.client.post(
            '/account/confirm_email/%s/%s/' % (ec.id, ec.token),
            {'new_password1': password,
             'new_password2': password})

        self.assertFalse(EmailConfirmation.objects.filter(pk=ec.pk).exists())
        self.assertTrue(User.objects.get(email=email).check_password(password))
        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(302, response.status_code)

    def test_confirm_existing_email_and_dont_set_password(self):
        email = 'email@example.com'
        password = 's0m3 P4sSw0rd'
        user = User.objects.create(email=email)
        user.set_password(password)
        user.save()

        initial_user_count = User.objects.count()

        ec = EmailConfirmation.objects.create(email=email)

        response = self.client.post(
            '/account/confirm_email/%s/%s/' % (ec.id, ec.token),
            {'no_password': True})

        self.assertFalse(EmailConfirmation.objects.filter(pk=ec.pk).exists())
        self.assertTrue(User.objects.get(email=email).check_password(password))
        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(302, response.status_code)

    def test_non_existant_token(self):
        initial_user_count = User.objects.count()
        initial_email_confirmation_count = EmailConfirmation.objects.count()

        response = self.client.post(
            '/account/confirm_email/%s/%s/' % ('123', 'a798797b8979c7f890'),
            {'nopassword': None})

        self.assertEqual(200, response.status_code)
        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(
            initial_email_confirmation_count,
            EmailConfirmation.objects.count())

    def test_confirmation_link_expired(self):
        email = 'email@example.com'
        password = 's0m3 P4sSw0rd'
        initial_user_count = User.objects.count()

        self.assertFalse(User.objects.filter(email=email).exists())

        valid_until = timezone.now() - datetime.timedelta(days=1)

        ec = EmailConfirmation.objects.create(email=email,
                                              valid_until=valid_until)

        response = self.client.post(
            '/account/confirm_email/%s/%s/' % (ec.id, ec.token),
            {'new_password1': password,
             'new_password2': password})

        self.assertEqual(initial_user_count, User.objects.count())
        self.assertEqual(200, response.status_code)
