from django.utils.translation import ugettext as _

import graphene
from graphene.types.generic import GenericScalar

from . import exceptions
from .decorators import setup_jwt_cookie
from .refresh_token.mixins import RefreshTokenMixin
from .settings import jwt_settings
from .utils import get_payload, get_user_by_payload


class JSONWebTokenMixin(object):
    token = graphene.String()

    @classmethod
    def Field(cls, *args, **kwargs):
        if jwt_settings.JWT_LONG_RUNNING_REFRESH_TOKEN:
            cls._meta.fields['refresh_token'] = graphene.Field(graphene.String)

        return super(JSONWebTokenMixin, cls).Field(*args, **kwargs)


class ObtainJSONWebTokenMixin(JSONWebTokenMixin):

    @classmethod
    def __init_subclass_with_meta__(cls, name=None, **options):
        assert getattr(cls, 'resolve', None), (
            '{name}.resolve method is required in a JSONWebTokenMutation.'
        ).format(name=name or cls.__name__)

        super(ObtainJSONWebTokenMixin, cls)\
            .__init_subclass_with_meta__(name=name, **options)


class VerifyMixin(object):
    payload = GenericScalar()


class ResolveMixin(object):

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls()


class KeepAliveRefreshMixin(object):

    class Fields:
        token = graphene.String(required=True)

    @classmethod
    @setup_jwt_cookie
    def refresh(cls, root, info, token, **kwargs):
        context = info.context
        payload = get_payload(token, context)
        user = get_user_by_payload(payload)
        orig_iat = payload.get('origIat')

        if not orig_iat:
            raise exceptions.JSONWebTokenError(_('origIat field is required'))

        if jwt_settings.JWT_REFRESH_EXPIRED_HANDLER(orig_iat, context):
            raise exceptions.JSONWebTokenError(_('Refresh has expired'))

        payload = jwt_settings.JWT_PAYLOAD_HANDLER(user, context)
        payload['origIat'] = orig_iat

        token = jwt_settings.JWT_ENCODE_HANDLER(payload, context)
        return cls(token=token, payload=payload)


class RefreshMixin((RefreshTokenMixin
                    if jwt_settings.JWT_LONG_RUNNING_REFRESH_TOKEN
                    else KeepAliveRefreshMixin),
                   JSONWebTokenMixin):

    payload = GenericScalar()
