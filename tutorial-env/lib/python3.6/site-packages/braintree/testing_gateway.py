import braintree
from braintree.error_result import ErrorResult
from braintree.successful_result import SuccessfulResult
from braintree.transaction import Transaction
from braintree.exceptions.test_operation_performed_in_production_error import TestOperationPerformedInProductionError

class TestingGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def make_past_due(self, subscription_id, number_of_days_past_due=1):
        self.__check_environment()
        self.config.http().put(self.config.base_merchant_path() + "/subscriptions/%s/make_past_due?days_past_due=%s" % (subscription_id, number_of_days_past_due))

    def escrow_transaction(self, transaction_id):
        self.__check_environment()
        self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/escrow")

    def settle_transaction(self, transaction_id):
        self.__check_environment()
        return self.__create_result(self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/settle"))

    def settlement_confirm_transaction(self, transaction_id):
        self.__check_environment()
        return self.__create_result(self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/settlement_confirm"))

    def settlement_decline_transaction(self, transaction_id):
        self.__check_environment()
        return self.__create_result(self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/settlement_decline"))

    def settlement_pending_transaction(self, transaction_id):
        self.__check_environment()
        return self.__create_result(self.config.http().put(self.config.base_merchant_path() + "/transactions/" + transaction_id + "/settlement_pending"))

    def create_3ds_verification(self, merchant_account_id, params):
        self.__check_environment()
        response = self.config.http().post(self.config.base_merchant_path() + "/three_d_secure/create_verification/" + merchant_account_id, {
            "three_d_secure_verification": params
        })
        return response["three_d_secure_verification"]["three_d_secure_token"]

    def __create_result(self, response):
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(self.gateway, response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(self.gateway, response["api_error_response"])

    def __check_environment(self):
        if self.config.environment == braintree.Environment.Production:
            raise TestOperationPerformedInProductionError()

