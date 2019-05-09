from calendar import timegm
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

import jwt

from . import exceptions
from .settings import jwt_settings


def jwt_payload(user, context=None):
    username = user.get_username()

    if hasattr(username, 'pk'):
        username = username.pk

    payload = {
        user.USERNAME_FIELD: username,
        'exp': datetime.utcnow() + jwt_settings.JWT_EXPIRATION_DELTA,
    }

    if jwt_settings.JWT_ALLOW_REFRESH:
        payload['origIat'] = timegm(datetime.utcnow().utctimetuple())

    if jwt_settings.JWT_AUDIENCE is not None:
        payload['aud'] = jwt_settings.JWT_AUDIENCE

    if jwt_settings.JWT_ISSUER is not None:
        payload['iss'] = jwt_settings.JWT_ISSUER

    return payload


def jwt_encode(payload, context=None):
    return jwt.encode(
        payload,
        jwt_settings.JWT_SECRET_KEY,
        jwt_settings.JWT_ALGORITHM,
    ).decode('utf-8')


def jwt_decode(token, context=None):
    return jwt.decode(
        token,
        jwt_settings.JWT_SECRET_KEY,
        jwt_settings.JWT_VERIFY,
        options={
            'verify_exp': jwt_settings.JWT_VERIFY_EXPIRATION,
        },
        leeway=jwt_settings.JWT_LEEWAY,
        audience=jwt_settings.JWT_AUDIENCE,
        issuer=jwt_settings.JWT_ISSUER,
        algorithms=[jwt_settings.JWT_ALGORITHM])


def get_http_authorization(request):
    auth = request.META.get(jwt_settings.JWT_AUTH_HEADER_NAME, '').split()
    prefix = jwt_settings.JWT_AUTH_HEADER_PREFIX

    if len(auth) != 2 or auth[0].lower() != prefix.lower():
        return request.COOKIES.get(jwt_settings.JWT_COOKIE_NAME)
    return auth[1]


def get_token_argument(request, **kwargs):
    if jwt_settings.JWT_ALLOW_ARGUMENT:
        input_fields = kwargs.get('input')

        if isinstance(input_fields, dict):
            kwargs = input_fields

        return kwargs.get(jwt_settings.JWT_ARGUMENT_NAME)
    return None


def get_credentials(request, **kwargs):
    return (get_token_argument(request, **kwargs) or
            get_http_authorization(request))


def get_payload(token, context=None):
    try:
        payload = jwt_settings.JWT_DECODE_HANDLER(token, context)
    except jwt.ExpiredSignature:
        raise exceptions.JSONWebTokenExpired()
    except jwt.DecodeError:
        raise exceptions.JSONWebTokenError(_('Error decoding signature'))
    except jwt.InvalidTokenError:
        raise exceptions.JSONWebTokenError(_('Invalid token'))
    return payload


def get_user_by_natural_key(user_id):
    User = get_user_model()
    try:
        return User.objects.get_by_natural_key(user_id)
    except User.DoesNotExist:
        return None


def get_user_by_payload(payload):
    username = jwt_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER(payload)

    if not username:
        raise exceptions.JSONWebTokenError(_('Invalid payload'))

    user = get_user_by_natural_key(username)

    if user is not None and not user.is_active:
        raise exceptions.JSONWebTokenError(_('User is disabled'))
    return user


def refresh_has_expired(orig_iat, context=None):
    return timegm(datetime.utcnow().utctimetuple()) > (
        orig_iat + jwt_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()
    )
