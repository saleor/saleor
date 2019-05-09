import braintree
from braintree.credit_card import CreditCard
from braintree.error_result import ErrorResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.ids_search import IdsSearch
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult
from braintree.transparent_redirect import TransparentRedirect

class CreditCardGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def confirm_transparent_redirect(self, query_string):
        id = self.gateway.transparent_redirect._parse_and_validate_query_string(query_string)["id"][0]
        return self._post("/payment_methods/all/confirm_transparent_redirect_request", {"id": id})

    def create(self, params={}):
        Resource.verify_keys(params, CreditCard.create_signature())
        return self._post("/payment_methods", {"credit_card": params})

    def delete(self, credit_card_token):
        self.config.http().delete(self.config.base_merchant_path() + "/payment_methods/credit_card/" + credit_card_token)
        return SuccessfulResult()

    def expired(self):
        response = self.config.http().post(self.config.base_merchant_path() + "/payment_methods/all/expired_ids")
        return ResourceCollection(None, response, self.__fetch_expired)

    def expiring_between(self, start_date, end_date):
        formatted_start_date = start_date.strftime("%m%Y")
        formatted_end_date = end_date.strftime("%m%Y")
        query = "start=%s&end=%s" % (formatted_start_date, formatted_end_date)
        response = self.config.http().post(self.config.base_merchant_path() + "/payment_methods/all/expiring_ids?" + query)
        return ResourceCollection(query, response, self.__fetch_existing_between)

    def find(self, credit_card_token):
        try:
            if credit_card_token is None or credit_card_token.strip() == "":
                raise NotFoundError()
            response = self.config.http().get(self.config.base_merchant_path() + "/payment_methods/credit_card/" + credit_card_token)
            return CreditCard(self.gateway, response["credit_card"])
        except NotFoundError:
            raise NotFoundError("payment method with token " + repr(credit_card_token) + " not found")

    def forward(self, credit_card_token, receiving_merchant_id):
        raise NotFoundError("This method of forwarding payment methods is no longer supported. Please consider the Grant API for similar functionality.")

    def from_nonce(self, nonce):
        try:
            if nonce is None or nonce.strip() == "":
                raise NotFoundError()
            response = self.config.http().get(self.config.base_merchant_path() + "/payment_methods/from_nonce/" + nonce)
            return CreditCard(self.gateway, response["credit_card"])
        except NotFoundError:
            raise NotFoundError("payment method with nonce " + nonce + " locked, consumed or not found")

    def tr_data_for_create(self, tr_data, redirect_url):
        Resource.verify_keys(tr_data, [{"credit_card": CreditCard.create_signature()}])
        tr_data["kind"] = TransparentRedirect.Kind.CreatePaymentMethod
        return self.gateway.transparent_redirect.tr_data(tr_data, redirect_url)

    def tr_data_for_update(self, tr_data, redirect_url):
        Resource.verify_keys(tr_data, ["payment_method_token", {"credit_card": CreditCard.update_signature()}])
        tr_data["kind"] = TransparentRedirect.Kind.UpdatePaymentMethod
        return self.gateway.transparent_redirect.tr_data(tr_data, redirect_url)

    def transparent_redirect_create_url(self):
        return self.config.base_url() + self.config.base_merchant_path() + "/payment_methods/all/create_via_transparent_redirect_request"

    def transparent_redirect_update_url(self):
        return self.config.base_url() + self.config.base_merchant_path() + "/payment_methods/all/update_via_transparent_redirect_request"

    def update(self, credit_card_token, params={}):
        Resource.verify_keys(params, CreditCard.update_signature())
        response = self.config.http().put(self.config.base_merchant_path() + "/payment_methods/credit_card/" + credit_card_token, {"credit_card": params})
        if "credit_card" in response:
            return SuccessfulResult({"credit_card": CreditCard(self.gateway, response["credit_card"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def __fetch_expired(self, query, ids):
        criteria = {}
        criteria["ids"] = IdsSearch.ids.in_list(ids).to_param()
        response = self.config.http().post(self.config.base_merchant_path() + "/payment_methods/all/expired", {"search": criteria})
        return [CreditCard(self.gateway, item) for item in ResourceCollection._extract_as_array(response["payment_methods"], "credit_card")]

    def __fetch_existing_between(self, query, ids):
        criteria = {}
        criteria["ids"] = IdsSearch.ids.in_list(ids).to_param()
        response = self.config.http().post(self.config.base_merchant_path() + "/payment_methods/all/expiring?" + query, {"search": criteria})
        return [CreditCard(self.gateway, item) for item in ResourceCollection._extract_as_array(response["payment_methods"], "credit_card")]

    def _post(self, url, params={}):
        response = self.config.http().post(self.config.base_merchant_path() + url, params)
        if "credit_card" in response:
            return SuccessfulResult({"credit_card": CreditCard(self.gateway, response["credit_card"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

