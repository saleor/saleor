# -*- coding: utf-8 -*-
"""
oauthlib.openid.connect.core.grant_types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, unicode_literals

import logging

from .base import GrantTypeBase

from oauthlib.oauth2.rfc6749.grant_types.implicit import ImplicitGrant as OAuth2ImplicitGrant

log = logging.getLogger(__name__)


class ImplicitGrant(GrantTypeBase):

    def __init__(self, request_validator=None, **kwargs):
        self.proxy_target = OAuth2ImplicitGrant(
            request_validator=request_validator, **kwargs)
        self.register_response_type('id_token')
        self.register_response_type('id_token token')
        self.custom_validators.post_auth.append(
            self.openid_authorization_validator)
        self.custom_validators.post_auth.append(
            self.openid_implicit_authorization_validator)
        self.register_token_modifier(self.add_id_token)
