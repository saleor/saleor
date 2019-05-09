from calendar import timegm

from django.utils.translation import ugettext as _

import graphene

from .. import exceptions
from ..decorators import setup_jwt_cookie
from ..settings import jwt_settings
from .shortcuts import get_refresh_token, refresh_token_lazy


class RefreshTokenMixin(object):

    class Fields:
        refresh_token = graphene.String(required=True)

    @classmethod
    @setup_jwt_cookie
    def refresh(cls, root, info, refresh_token, **kwargs):
        context = info.context
        refresh_token = get_refresh_token(refresh_token, info.context)

        if refresh_token.is_expired(context):
            raise exceptions.JSONWebTokenError(_('Refresh token is expired'))

        payload = jwt_settings.JWT_PAYLOAD_HANDLER(refresh_token.user, context)
        token = jwt_settings.JWT_ENCODE_HANDLER(payload, context)

        refresh_token.rotate()
        refreshed_token = refresh_token_lazy(refresh_token.user)
        return cls(token=token, payload=payload, refresh_token=refreshed_token)


class RevokeMixin(object):
    revoked = graphene.Int()

    @classmethod
    def revoke(cls, root, info, refresh_token, **kwargs):
        refresh_token = get_refresh_token(refresh_token, info.context)
        refresh_token.revoke()
        return cls(revoked=timegm(refresh_token.revoked.timetuple()))
