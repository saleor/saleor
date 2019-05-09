import braintree
from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult
from braintree.transaction import Transaction
from braintree.transparent_redirect import TransparentRedirect
from braintree.exceptions.not_found_error import NotFoundError
from braintree.exceptions.down_for_maintenance_error import DownForMaintenanceError

class TransactionGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def clone_transaction(self, transaction_id, params):
        Resource.verify_keys(params, Transaction.clone_signature())
        return self._post("/transactions/" + transaction_id + "/clone", {"transaction-clone": params})

    def cancel_release(self, transaction_id):
        response = self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/cancel_release", {})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def confirm_transparent_redirect(self, query_string):
        id = self.gateway.transparent_redirect._parse_and_validate_query_string(query_string)["id"][0]
        return self._post("/transactions/all/confirm_transparent_redirect_request", {"id": id})

    def create(self, params):
        Resource.verify_keys(params, Transaction.create_signature())
        return self._post("/transactions", {"transaction": params})

    def find(self, transaction_id):
        try:
            if transaction_id is None or transaction_id.strip() == "":
                raise NotFoundError()
            response = self.config.http().get(self.config.base_merchant_path() + "/transactions/" + transaction_id)
            return Transaction(self.gateway, response["transaction"])
        except NotFoundError:
            raise NotFoundError("transaction with id " + repr(transaction_id) + " not found")

    def hold_in_escrow(self, transaction_id):
        """
        Holds an existing submerchant transaction for escrow. It expects a transaction_id. ::

            result = braintree.Transaction.hold_in_escrow("my_transaction_id")
        """

        response = self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/hold_in_escrow", {})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def refund(self, transaction_id, amount_or_options=None):
        """
        Refunds an existing transaction. It expects a transaction_id. ::

            result = braintree.Transaction.refund("my_transaction_id")
        """
        if isinstance(amount_or_options, dict):
            options = amount_or_options
        else:
            options = {
                "amount": amount_or_options
            }
        Resource.verify_keys(options, Transaction.refund_signature())
        response = self.config.http().post(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/refund", {"transaction": options})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def sale(self, params):
        params.update({"type": "sale"})
        return self.create(params)

    def search(self, *query):
        if isinstance(query[0], list):
            query = query[0]

        response = self.config.http().post(self.config.base_merchant_path() + "/transactions/advanced_search_ids", {"search": self.__criteria(query)})
        if "search_results" in response:
            return ResourceCollection(query, response, self.__fetch)
        else:
            raise DownForMaintenanceError("search timeout")

    def release_from_escrow(self, transaction_id):
        response = self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/release_from_escrow", {})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def submit_for_settlement(self, transaction_id, amount=None, params={}):
        Resource.verify_keys(params, Transaction.submit_for_settlement_signature())
        transaction_params = {"amount": amount}
        transaction_params.update(params)
        response = self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/submit_for_settlement",
                {"transaction": transaction_params})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def update_details(self, transaction_id, params={}):
        Resource.verify_keys(params, Transaction.update_details_signature())
        response = self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/update_details",
                {"transaction": params})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def submit_for_partial_settlement(self, transaction_id, amount, params={}):
        Resource.verify_keys(params, Transaction.submit_for_settlement_signature())
        transaction_params = {"amount": amount}
        transaction_params.update(params)
        response = self.config.http().post(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/submit_for_partial_settlement",
                {"transaction": transaction_params})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def tr_data_for_credit(self, tr_data, redirect_url):
        if "transaction" not in tr_data:
            tr_data["transaction"] = {}
        tr_data["transaction"]["type"] = Transaction.Type.Credit
        Resource.verify_keys(tr_data, [{"transaction": Transaction.create_signature()}])
        tr_data["kind"] = TransparentRedirect.Kind.CreateTransaction
        return self.gateway.transparent_redirect.tr_data(tr_data, redirect_url)

    def tr_data_for_sale(self, tr_data, redirect_url):
        if "transaction" not in tr_data:
            tr_data["transaction"] = {}
        tr_data["transaction"]["type"] = Transaction.Type.Sale
        Resource.verify_keys(tr_data, [{"transaction": Transaction.create_signature()}])
        tr_data["kind"] = TransparentRedirect.Kind.CreateTransaction
        return self.gateway.transparent_redirect.tr_data(tr_data, redirect_url)

    def transparent_redirect_create_url(self):
        return self.config.base_url() + self.config.base_merchant_path() + "/transactions/all/create_via_transparent_redirect_request"

    def void(self, transaction_id):
        response = self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/void")
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def __fetch(self, query, ids):
        criteria = self.__criteria(query)
        criteria["ids"] = braintree.transaction_search.TransactionSearch.ids.in_list(ids).to_param()
        response = self.config.http().post(self.config.base_merchant_path() + "/transactions/advanced_search", {"search": criteria})
        if "credit_card_transactions" in response:
            return [Transaction(self.gateway, item) for item in ResourceCollection._extract_as_array(response["credit_card_transactions"], "transaction")]
        else:
            raise DownForMaintenanceError("search timeout")

    def __criteria(self, query):
        criteria = {}
        for term in query:
            if criteria.get(term.name):
                criteria[term.name] = dict(list(criteria[term.name].items()) + list(term.to_param().items()))
            else:
                criteria[term.name] = term.to_param()
        return criteria

    def _post(self, url, params={}):
        response = self.config.http().post(self.config.base_merchant_path() + url, params)
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

