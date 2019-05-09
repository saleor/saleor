import cgi
from datetime import datetime
import braintree
from braintree.util.crypto import Crypto
from braintree.error_result import ErrorResult
from braintree.exceptions.forged_query_string_error import ForgedQueryStringError
from braintree.util.http import Http
from braintree.signature_service import SignatureService
from braintree.successful_result import SuccessfulResult
from braintree.transparent_redirect import TransparentRedirect

class TransparentRedirectGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def confirm(self, query_string):
        """
        Confirms a transparent redirect request. It expects the query string from the
        redirect request. The query string should _not_ include the leading "?" character. ::

            result = braintree.TransparentRedirect.confirm("foo=bar&id=12345")
        """
        parsed_query_string = self._parse_and_validate_query_string(query_string)
        confirmation_gateway = {
            TransparentRedirect.Kind.CreateCustomer: "customer",
            TransparentRedirect.Kind.UpdateCustomer: "customer",
            TransparentRedirect.Kind.CreatePaymentMethod: "credit_card",
            TransparentRedirect.Kind.UpdatePaymentMethod: "credit_card",
            TransparentRedirect.Kind.CreateTransaction: "transaction"
        }[parsed_query_string["kind"][0]]

        return getattr(self.gateway, confirmation_gateway)._post("/transparent_redirect_requests/" + parsed_query_string["id"][0] + "/confirm")

    def tr_data(self, data, redirect_url):
        data = self.__flatten_dictionary(data)
        date_string = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        data["time"] = date_string
        data["redirect_url"] = redirect_url
        data["public_key"] = self.config.public_key
        data["api_version"] = self.config.api_version()

        return SignatureService(self.config.private_key).sign(data)

    def url(self):
        """
        Returns the url for POSTing Transparent Redirect HTML forms
        """
        return self.config.base_url() + self.config.base_merchant_path() + "/transparent_redirect_requests"

    def _parse_and_validate_query_string(self, query_string):
        query_params = cgi.parse_qs(query_string)
        http_status = int(query_params["http_status"][0])
        message = query_params.get("bt_message")
        if message is not None:
            message = message[0]

        if Http.is_error_status(http_status):
            Http.raise_exception_from_status(http_status, message)

        if not self._is_valid_tr_query_string(query_string):
            raise ForgedQueryStringError

        return query_params

    def _is_valid_tr_query_string(self, query_string):
        content, hash = query_string.split("&hash=")
        return hash == Crypto.sha1_hmac_hash(self.config.private_key, content)

    def __flatten_dictionary(self, params, parent=None):
        data = {}
        for key, val in params.items():
            full_key = parent + "[" + key + "]" if parent else key
            if isinstance(val, dict):
                data.update(self.__flatten_dictionary(val, full_key))
            else:
                data[full_key] = val
        return data

