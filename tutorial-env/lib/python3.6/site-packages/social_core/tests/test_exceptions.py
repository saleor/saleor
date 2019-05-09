import unittest2 as unittest

from ..exceptions import SocialAuthBaseException, WrongBackend, \
                         AuthFailed, AuthTokenError, \
                         AuthMissingParameter, AuthStateMissing, \
                         NotAllowedToDisconnect, AuthException, \
                         AuthCanceled, AuthUnknownError, \
                         AuthStateForbidden, AuthAlreadyAssociated, \
                         AuthTokenRevoked, AuthForbidden, \
                         AuthUnreachableProvider, InvalidEmail, \
                         MissingBackend


class BaseExceptionTestCase(unittest.TestCase):
    exception = None
    expected_message = ''

    def test_exception_message(self):
        if self.exception is None and self.expected_message == '':
            return
        try:
            raise self.exception
        except SocialAuthBaseException as err:
            self.assertEqual(str(err), self.expected_message)


class WrongBackendTest(BaseExceptionTestCase):
    exception = WrongBackend('foobar')
    expected_message = 'Incorrect authentication service "foobar"'


class AuthFailedTest(BaseExceptionTestCase):
    exception = AuthFailed('foobar', 'wrong_user')
    expected_message = 'Authentication failed: wrong_user'


class AuthFailedDeniedTest(BaseExceptionTestCase):
    exception = AuthFailed('foobar', 'access_denied')
    expected_message = 'Authentication process was canceled'


class AuthTokenErrorTest(BaseExceptionTestCase):
    exception = AuthTokenError('foobar', 'Incorrect tokens')
    expected_message = 'Token error: Incorrect tokens'


class AuthMissingParameterTest(BaseExceptionTestCase):
    exception = AuthMissingParameter('foobar', 'username')
    expected_message = 'Missing needed parameter username'


class AuthStateMissingTest(BaseExceptionTestCase):
    exception = AuthStateMissing('foobar')
    expected_message = 'Session value state missing.'


class NotAllowedToDisconnectTest(BaseExceptionTestCase):
    exception = NotAllowedToDisconnect()
    expected_message = ''


class AuthExceptionTest(BaseExceptionTestCase):
    exception = AuthException('foobar', 'message')
    expected_message = 'message'


class AuthCanceledTest(BaseExceptionTestCase):
    exception = AuthCanceled('foobar')
    expected_message = 'Authentication process canceled'


class AuthCanceledWithExtraMessageTest(BaseExceptionTestCase):
    exception = AuthCanceled('foobar', 'error_message')
    expected_message = 'Authentication process canceled: error_message'


class AuthUnknownErrorTest(BaseExceptionTestCase):
    exception = AuthUnknownError('foobar', 'some error')
    expected_message = 'An unknown error happened while ' \
                       'authenticating some error'


class AuthStateForbiddenTest(BaseExceptionTestCase):
    exception = AuthStateForbidden('foobar')
    expected_message = 'Wrong state parameter given.'


class AuthAlreadyAssociatedTest(BaseExceptionTestCase):
    exception = AuthAlreadyAssociated('foobar')
    expected_message = ''


class AuthTokenRevokedTest(BaseExceptionTestCase):
    exception = AuthTokenRevoked('foobar')
    expected_message = 'User revoke access to the token'


class AuthForbiddenTest(BaseExceptionTestCase):
    exception = AuthForbidden('foobar')
    expected_message = 'Your credentials aren\'t allowed'


class AuthUnreachableProviderTest(BaseExceptionTestCase):
    exception = AuthUnreachableProvider('foobar')
    expected_message = 'The authentication provider could not be reached'


class InvalidEmailTest(BaseExceptionTestCase):
    exception = InvalidEmail('foobar')
    expected_message = 'Email couldn\'t be validated'


class MissingBackendTest(BaseExceptionTestCase):
    exception = MissingBackend('backend')
    expected_message = 'Missing backend "backend" entry'
