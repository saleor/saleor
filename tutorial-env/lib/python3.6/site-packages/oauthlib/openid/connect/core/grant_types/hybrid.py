# -*- coding: utf-8 -*-
"""
oauthlib.openid.connect.core.grant_types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, unicode_literals

import logging

from oauthlib.oauth2.rfc6749.grant_types.authorization_code import AuthorizationCodeGrant as OAuth2AuthorizationCodeGrant

from .base import GrantTypeBase
from ..request_validator import RequestValidator

log = logging.getLogger(__name__)


class HybridGrant(GrantTypeBase):

    def __init__(self, request_validator=None, **kwargs):
        self.request_validator = request_validator or RequestValidator()

        self.proxy_target = OAuth2AuthorizationCodeGrant(
            request_validator=request_validator, **kwargs)
        # All hybrid response types should be fragment-encoded.
        self.proxy_target.default_response_mode = "fragment"
        self.register_response_type('code id_token')
        self.register_response_type('code token')
        self.register_response_type('code id_token token')
        self.custom_validators.post_auth.append(
            self.openid_authorization_validator)
        # Hybrid flows can return the id_token from the authorization
        # endpoint as part of the 'code' response
        self.register_code_modifier(self.add_token)
        self.register_code_modifier(self.add_id_token)
        self.register_token_modifier(self.add_id_token)
