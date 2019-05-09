import json

from braintree.exceptions.authentication_error import AuthenticationError
from braintree.exceptions.authorization_error import AuthorizationError
from braintree.exceptions.down_for_maintenance_error import DownForMaintenanceError
from braintree.exceptions.not_found_error import NotFoundError
from braintree.exceptions.server_error import ServerError
from braintree.exceptions.too_many_requests_error import TooManyRequestsError
from braintree.exceptions.unexpected_error import UnexpectedError
from braintree.exceptions.upgrade_required_error import UpgradeRequiredError
from braintree.util.http import Http

class GraphQLClient(Http):

    @staticmethod
    def raise_exception_for_graphql_error(response):
        if "errors" not in response:
            return

        for error in response["errors"]:
            if "extensions" in error and "errorClass" in error["extensions"]:
                error_type = error["extensions"]["errorClass"]
                if error_type == "VALIDATION":
                    continue
                elif error_type == "AUTHENTICATION":
                    raise AuthenticationError(error["message"])
                elif error_type == "AUTHORIZATION":
                    raise AuthorizationError(error["message"])
                elif error_type == "NOT_FOUND":
                    raise NotFoundError
                elif error_type == "UNSUPPORTED_CLIENT":
                    raise UpgradeRequiredError("Please upgrade your client library.")
                elif error_type == "RESOURCE_LIMIT":
                    raise TooManyRequestsError
                elif error_type == "INTERNAL":
                    raise ServerError
                elif error_type == "SERVICE_AVAILABILITY":
                    raise DownForMaintenanceError
                else:
                    raise UnexpectedError("Unexpected Response: " + error["message"])

    def __init__(self, config=None, environment=None):
        Http.__init__(self, config, environment)
        self.graphql_headers = {
            "Accept": "application/json",
            "Braintree-Version": config.graphql_api_version(),
            "Content-Type": "application/json"
        }

    def query(self, definition, variables=None, operation_name=None):
        graphql_request = {
            "query": definition
        }

        if variables is not None:
            graphql_request["variables"] = variables

        if operation_name is not None:
            graphql_request["operationName"] = operation_name

        response = self._make_request("POST", self.config.graphql_base_url(),
                                      Http.ContentType.Json, json.dumps(graphql_request),
                                      header_overrides=self.graphql_headers)
        self.raise_exception_for_graphql_error(response)

        return response
