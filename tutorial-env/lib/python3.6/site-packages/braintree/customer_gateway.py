import braintree
from braintree.customer import Customer
from braintree.error_result import ErrorResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.ids_search import IdsSearch
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult
from braintree.transparent_redirect import TransparentRedirect

class CustomerGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def all(self):
        response = self.config.http().post(self.config.base_merchant_path() + "/customers/advanced_search_ids")
        return ResourceCollection({}, response, self.__fetch)

    def confirm_transparent_redirect(self, query_string):
        id = self.gateway.transparent_redirect._parse_and_validate_query_string(query_string)["id"][0]
        return self._post("/customers/all/confirm_transparent_redirect_request", {"id": id})

    def create(self, params={}):
        Resource.verify_keys(params, Customer.create_signature())
        return self._post("/customers", {"customer": params})

    def delete(self, customer_id):
        self.config.http().delete(self.config.base_merchant_path() + "/customers/" + customer_id)
        return SuccessfulResult()

    def find(self, customer_id, association_filter_id=None):
        try:
            if customer_id is None or customer_id.strip() == "":
                raise NotFoundError()

            query_params = ""
            if association_filter_id:
                query_params = "?association_filter_id=" + association_filter_id

            response = self.config.http().get(self.config.base_merchant_path() + "/customers/" + customer_id + query_params)
            return Customer(self.gateway, response["customer"])
        except NotFoundError:
            raise NotFoundError("customer with id " + repr(customer_id) + " not found")

    def search(self, *query):
        if isinstance(query[0], list):
            query = query[0]

        response = self.config.http().post(self.config.base_merchant_path() + "/customers/advanced_search_ids", {"search": self.__criteria(query)})
        return ResourceCollection(query, response, self.__fetch)

    def tr_data_for_create(self, tr_data, redirect_url):
        Resource.verify_keys(tr_data, [{"customer": Customer.create_signature()}])
        tr_data["kind"] = TransparentRedirect.Kind.CreateCustomer
        return self.gateway.transparent_redirect.tr_data(tr_data, redirect_url)

    def tr_data_for_update(self, tr_data, redirect_url):
        Resource.verify_keys(tr_data, ["customer_id", {"customer": Customer.update_signature()}])
        tr_data["kind"] = TransparentRedirect.Kind.UpdateCustomer
        return self.gateway.transparent_redirect.tr_data(tr_data, redirect_url)

    def transparent_redirect_create_url(self):
        return self.config.base_url() + self.config.base_merchant_path() + "/customers/all/create_via_transparent_redirect_request"

    def transparent_redirect_update_url(self):
        return self.config.base_url() + self.config.base_merchant_path() + "/customers/all/update_via_transparent_redirect_request"

    def update(self, customer_id, params={}):
        Resource.verify_keys(params, Customer.update_signature())
        response = self.config.http().put(self.config.base_merchant_path() + "/customers/" + customer_id, {"customer": params})
        if "customer" in response:
            return SuccessfulResult({"customer": Customer(self.gateway, response["customer"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def __criteria(self, query):
        criteria = {}
        for term in query:
            if criteria.get(term.name):
                criteria[term.name] = dict(list(criteria[term.name].items()) + list(term.to_param().items()))
            else:
                criteria[term.name] = term.to_param()
        return criteria

    def __fetch(self, query, ids):
        criteria = self.__criteria(query)
        criteria["ids"] = braintree.customer_search.CustomerSearch.ids.in_list(ids).to_param()
        response = self.config.http().post(self.config.base_merchant_path() + "/customers/advanced_search", {"search": criteria})
        return [Customer(self.gateway, item) for item in ResourceCollection._extract_as_array(response["customers"], "customer")]

    def _post(self, url, params={}):
        response = self.config.http().post(self.config.base_merchant_path() + url, params)
        if "customer" in response:
            return SuccessfulResult({"customer": Customer(self.gateway, response["customer"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])
        else:
            pass

