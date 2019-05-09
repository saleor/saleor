"""Models mixins for Social Auth"""
import re
import time
import base64
import uuid
import warnings

from datetime import datetime, timedelta

import six

from openid.association import Association as OpenIdAssociation

from .exceptions import MissingBackend
from .backends.utils import get_backend


NO_ASCII_REGEX = re.compile(r'[^\x00-\x7F]+')
NO_SPECIAL_REGEX = re.compile(r'[^\w.@+_-]+', re.UNICODE)


class UserMixin(object):
    # Consider tokens that expire in 5 seconds as already expired
    ACCESS_TOKEN_EXPIRED_THRESHOLD = 5

    user = ''
    provider = ''
    uid = None
    extra_data = None

    def get_backend(self, strategy):
        return get_backend(strategy.get_backends(), self.provider)

    def get_backend_instance(self, strategy):
        try:
            backend_class = self.get_backend(strategy)
        except MissingBackend:
            return None
        else:
            return backend_class(strategy=strategy)

    @property
    def access_token(self):
        """Return access_token stored in extra_data or None"""
        return self.extra_data.get('access_token')

    @property
    def tokens(self):
        warnings.warn('tokens is deprecated, use access_token instead')
        return self.access_token

    def refresh_token(self, strategy, *args, **kwargs):
        token = self.extra_data.get('refresh_token') or \
                self.extra_data.get('access_token')
        backend = self.get_backend(strategy)
        if token and backend and hasattr(backend, 'refresh_token'):
            backend = backend(strategy=strategy)
            response = backend.refresh_token(token, *args, **kwargs)
            extra_data = backend.extra_data(self,
                                            self.uid,
                                            response,
                                            self.extra_data)
            if self.set_extra_data(extra_data):
                self.save()

    def expiration_timedelta(self):
        """Return provider session live seconds. Returns a timedelta ready to
        use with session.set_expiry().

        If provider returns a timestamp instead of session seconds to live, the
        timedelta is inferred from current time (using UTC timezone). None is
        returned if there's no value stored or it's invalid.
        """
        if self.extra_data and 'expires' in self.extra_data:
            try:
                expires = int(self.extra_data.get('expires'))
            except (ValueError, TypeError):
                return None

            now = datetime.utcnow()

            # Detect if expires is a timestamp
            if expires > time.mktime(now.timetuple()):
                # expires is a datetime, return the remaining difference
                return datetime.utcfromtimestamp(expires) - now
            else:
                # expires is the time to live seconds since creation,
                # check against auth_time if present, otherwise return
                # the value
                auth_time = self.extra_data.get('auth_time')
                if auth_time:
                    reference = datetime.utcfromtimestamp(auth_time)
                    return (reference + timedelta(seconds=expires)) - now
                else:
                    return timedelta(seconds=expires)

    def expiration_datetime(self):
        # backward compatible alias
        return self.expiration_timedelta()

    def access_token_expired(self):
        """Return true / false if access token is already expired"""
        expiration = self.expiration_timedelta()
        return expiration and \
            expiration.total_seconds() <= self.ACCESS_TOKEN_EXPIRED_THRESHOLD

    def get_access_token(self, strategy):
        """Returns a valid access token."""
        if self.access_token_expired():
            self.refresh_token(strategy)
        return self.access_token

    def set_extra_data(self, extra_data=None):
        if extra_data and self.extra_data != extra_data:
            if self.extra_data and not isinstance(
                    self.extra_data, six.string_types):
                self.extra_data.update(extra_data)
            else:
                self.extra_data = extra_data
            return True

    @classmethod
    def clean_username(cls, value):
        """Clean username removing any unsupported character"""
        value = NO_ASCII_REGEX.sub('', value)
        value = NO_SPECIAL_REGEX.sub('', value)
        return value

    @classmethod
    def changed(cls, user):
        """The given user instance is ready to be saved"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def get_username(cls, user):
        """Return the username for given user"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def user_model(cls):
        """Return the user model"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def username_max_length(cls):
        """Return the max length for username"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def allowed_to_disconnect(cls, user, backend_name, association_id=None):
        """Return if it's safe to disconnect the social account for the
        given user"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def disconnect(cls, entry):
        """Disconnect the social account for the given user"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def user_exists(cls, *args, **kwargs):
        """
        Return True/False if a User instance exists with the given arguments.
        Arguments are directly passed to filter() manager method.
        """
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def create_user(cls, *args, **kwargs):
        """Create a user instance"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def get_user(cls, pk):
        """Return user instance for given id"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def get_users_by_email(cls, email):
        """Return users instances for given email address"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def get_social_auth(cls, provider, uid):
        """Return UserSocialAuth for given provider and uid"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def get_social_auth_for_user(cls, user, provider=None, id=None):
        """Return all the UserSocialAuth instances for given user"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def create_social_auth(cls, user, uid, provider):
        """Create a UserSocialAuth instance for given user"""
        raise NotImplementedError('Implement in subclass')


class NonceMixin(object):
    """One use numbers"""
    server_url = ''
    timestamp = 0
    salt = ''

    @classmethod
    def use(cls, server_url, timestamp, salt):
        """Create a Nonce instance"""
        raise NotImplementedError('Implement in subclass')


class AssociationMixin(object):
    """OpenId account association"""
    server_url = ''
    handle = ''
    secret = ''
    issued = 0
    lifetime = 0
    assoc_type = ''

    @classmethod
    def oids(cls, server_url, handle=None):
        kwargs = {'server_url': server_url}
        if handle is not None:
            kwargs['handle'] = handle
        return sorted([
            (assoc.id, cls.openid_association(assoc))
            for assoc in cls.get(**kwargs)
        ], key=lambda x: x[1].issued, reverse=True)

    @classmethod
    def openid_association(cls, assoc):
        secret = assoc.secret
        if not isinstance(secret, six.binary_type):
            secret = secret.encode()
        return OpenIdAssociation(assoc.handle, base64.decodestring(secret),
                                 assoc.issued, assoc.lifetime,
                                 assoc.assoc_type)

    @classmethod
    def store(cls, server_url, association):
        """Create an Association instance"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def get(cls, *args, **kwargs):
        """Get an Association instance"""
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def remove(cls, ids_to_delete):
        """Remove an Association instance"""
        raise NotImplementedError('Implement in subclass')


class CodeMixin(object):
    email = ''
    code = ''
    verified = False

    def verify(self):
        self.verified = True
        self.save()

    @classmethod
    def generate_code(cls):
        return uuid.uuid4().hex

    @classmethod
    def make_code(cls, email):
        code = cls()
        code.email = email
        code.code = cls.generate_code()
        code.verified = False
        code.save()
        return code

    @classmethod
    def get_code(cls, code):
        raise NotImplementedError('Implement in subclass')


class PartialMixin(object):
    token = ''
    data = ''
    next_step = ''
    backend = ''

    @property
    def args(self):
        return self.data.get('args', [])

    @args.setter
    def args(self, value):
        self.data['args'] = value

    @property
    def kwargs(self):
        return self.data.get('kwargs', {})

    @kwargs.setter
    def kwargs(self, value):
        self.data['kwargs'] = value

    def extend_kwargs(self, values):
        self.data['kwargs'].update(values)

    @classmethod
    def generate_token(cls):
        return uuid.uuid4().hex

    @classmethod
    def load(cls, token):
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def destroy(cls, token):
        raise NotImplementedError('Implement in subclass')

    @classmethod
    def prepare(cls, backend, next_step, data):
        partial = cls()
        partial.backend = backend
        partial.next_step = next_step
        partial.data = data
        partial.token = cls.generate_token()
        return partial

    @classmethod
    def store(cls, partial):
        partial.save()
        return partial


class BaseStorage(object):
    user = UserMixin
    nonce = NonceMixin
    association = AssociationMixin
    code = CodeMixin
    partial = PartialMixin

    @classmethod
    def is_integrity_error(cls, exception):
        """Check if given exception flags an integrity error in the DB"""
        raise NotImplementedError('Implement in subclass')
