import re
import braintree
from braintree.plan import Plan
from braintree.error_result import ErrorResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult

class PlanGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def all(self):
        response = self.config.http().get(self.config.base_merchant_path() + "/plans/")
        return [Plan(self.gateway, item) for item in ResourceCollection._extract_as_array(response, "plans")]
