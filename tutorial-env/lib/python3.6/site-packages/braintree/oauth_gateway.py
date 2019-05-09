import braintree
from braintree.error_result import ErrorResult
from braintree.successful_result import SuccessfulResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.oauth_credentials import OAuthCredentials

import sys
if sys.version_info[0] == 2:
    from urllib import quote_plus
else:
    from urllib.parse import quote_plus
    from functools import reduce

class OAuthGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def create_token_from_code(self, params):
        params["grant_type"] = "authorization_code"
        return self._create_token(params)

    def create_token_from_refresh_token(self, params):
        params["grant_type"] = "refresh_token"
        return self._create_token(params)

    def revoke_access_token(self, access_token):
        self.config.assert_has_client_credentials()
        response = self.config.http().post("/oauth/revoke_access_token", {
            "token": access_token
        })

        if "result" in response and response["result"]["success"]:
            return SuccessfulResult
        else:
            return ErrorResult(self.gateway, "could not revoke access token")

    def _create_token(self, params):
        self.config.assert_has_client_credentials()
        response = self.config.http().post("/oauth/access_tokens", {
            "credentials": params
        })

        if "credentials" in response:
            return SuccessfulResult({"credentials": OAuthCredentials(self.gateway, response["credentials"])})
        else:
            return ErrorResult(self.gateway, response["api_error_response"])

    def connect_url(self, raw_params):
        params = {"client_id": self.config.client_id}
        params.update(raw_params)
        user_params = self._sub_query(params, "user")
        business_params = self._sub_query(params, "business")

        def clean_values(accumulator, kv_pair):
            key, value = kv_pair
            if isinstance(value, list):
                accumulator += [(key + "[]", v) for v in value]
            else:
                accumulator += [(key, value)]
            return accumulator

        params = reduce(clean_values, params.items(), [])
        query = params + user_params + business_params
        query_string = "&".join(quote_plus(key) + "=" + quote_plus(value) for key, value in query)
        return self.config.environment.base_url + "/oauth/connect?" + query_string

    def _sub_query(self, params, root):
        if root in params:
            sub_query = params.pop(root)
        else:
            sub_query = {}
        query = [(root + "[" + key + "]", str(value)) for key, value in sub_query.items()]
        return query
