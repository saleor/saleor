from __future__ import absolute_import, division, print_function

from stripe import api_requestor, connect_api_base, error
from stripe.six.moves.urllib.parse import urlencode


class OAuth(object):
    @staticmethod
    def _set_client_id(params):
        if "client_id" in params:
            return

        from stripe import client_id

        if client_id:
            params["client_id"] = client_id
            return

        raise error.AuthenticationError(
            "No client_id provided. (HINT: set your client_id using "
            '"stripe.client_id = <CLIENT-ID>"). You can find your client_ids '
            "in your Stripe dashboard at "
            "https://dashboard.stripe.com/account/applications/settings, "
            "after registering your account as a platform. See "
            "https://stripe.com/docs/connect/standalone-accounts for details, "
            "or email support@stripe.com if you have any questions."
        )

    @staticmethod
    def authorize_url(**params):
        path = "/oauth/authorize"
        OAuth._set_client_id(params)
        if "response_type" not in params:
            params["response_type"] = "code"
        query = urlencode(list(api_requestor._api_encode(params)))
        url = connect_api_base + path + "?" + query
        return url

    @staticmethod
    def token(**params):
        requestor = api_requestor.APIRequestor(api_base=connect_api_base)
        response, api_key = requestor.request(
            "post", "/oauth/token", params, None
        )
        return response.data

    @staticmethod
    def deauthorize(**params):
        requestor = api_requestor.APIRequestor(api_base=connect_api_base)
        OAuth._set_client_id(params)
        response, api_key = requestor.request(
            "post", "/oauth/deauthorize", params, None
        )
        return response.data
