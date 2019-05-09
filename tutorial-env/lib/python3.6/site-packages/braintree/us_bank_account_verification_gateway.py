from braintree.us_bank_account_verification import UsBankAccountVerification
from braintree.us_bank_account_verification_search import UsBankAccountVerificationSearch
from braintree.exceptions.not_found_error import NotFoundError
from braintree.error_result import ErrorResult
from braintree.successful_result import SuccessfulResult
from braintree.resource_collection import ResourceCollection

class UsBankAccountVerificationGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def confirm_micro_transfer_amounts(self, verification_id, amounts):
        try:
            if verification_id is None or verification_id.strip() == "":
                raise NotFoundError()

            response = self.config.http().put(
                self.config.base_merchant_path() + "/us_bank_account_verifications/" + verification_id + "/confirm_micro_transfer_amounts",
                {
                    "us_bank_account_verification": {
                        "deposit_amounts": amounts,
                    }
                }
            )

            if "us_bank_account_verification" in response: return SuccessfulResult({
                    "us_bank_account_verification": UsBankAccountVerification(self.gateway, response["us_bank_account_verification"])
                })
            elif "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])
        except NotFoundError:
            raise NotFoundError("UsBankAccountVerification with id " + repr(verification_id) + " not found")

    def find(self, verification_id):
        try:
            if verification_id is None or verification_id.strip() == "":
                raise NotFoundError()

            response = self.config.http().get(
                self.config.base_merchant_path() + "/us_bank_account_verifications/" + verification_id
            )

            return UsBankAccountVerification(self.gateway, response["us_bank_account_verification"])
        except NotFoundError:
            raise NotFoundError("UsBankAccountVerification with id " + repr(verification_id) + " not found")

    def search(self, *query):
        if isinstance(query[0], list):
            query = query[0]

        response = self.config.http().post(
            self.config.base_merchant_path() + "/us_bank_account_verifications/advanced_search_ids",
            {"search": self.__criteria(query)}
        )

        return ResourceCollection(query, response, self.__fetch)

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

        criteria["ids"] = UsBankAccountVerificationSearch.ids.in_list(ids).to_param()

        response = self.config.http().post(
            self.config.base_merchant_path() + "/us_bank_account_verifications/advanced_search",
            {"search": criteria}
        )

        collection_array = ResourceCollection._extract_as_array(
            response["us_bank_account_verifications"],
            "us_bank_account_verification"
        )

        return [UsBankAccountVerification(self.gateway, item) for item in collection_array]
