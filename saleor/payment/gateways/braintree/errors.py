# We are NOT handling errors from:
#   - Braintree Marketplace
#   - Dispute
#   - Apple Pay
#   - OAuth
#   - Venmo
#   - Search
#   - Recurring Billing
#   - 3D Secure
#   - Customer
# as they are not currently supported.
#
# For the full list of errors please refer to:
# https://developers.braintreepayments.com/reference/general/validation-errors/all/python#transaction
from braintree.exceptions.authentication_error import AuthenticationError
from braintree.exceptions.authorization_error import AuthorizationError
from braintree.exceptions.gateway_timeout_error import GatewayTimeoutError
from braintree.exceptions.not_found_error import NotFoundError
from braintree.exceptions.request_timeout_error import RequestTimeoutError
from braintree.exceptions.server_error import ServerError
from braintree.exceptions.service_unavailable_error import ServiceUnavailableError
from braintree.exceptions.too_many_requests_error import TooManyRequestsError
from braintree.exceptions.upgrade_required_error import UpgradeRequiredError

DEFAULT_ERROR_MESSAGE = (
    "Unable to process the transaction. Transaction's token is incorrect or expired."
)


class BraintreeException(Exception):
    pass


BRAINTREE_ERROR_MESSAGES = {
    AuthenticationError: "Authentication error",
    AuthorizationError: "Authorization error",
    NotFoundError: DEFAULT_ERROR_MESSAGE,
    RequestTimeoutError: "Request timeout error",
    UpgradeRequiredError: "Upgrade required error",
    TooManyRequestsError: "Too many requests error",
    ServerError: "Server error",
    ServiceUnavailableError: "Server unavailable error",
    GatewayTimeoutError: "Gateway timeout error",
}


def handle_braintree_error(exc):
    msg = BRAINTREE_ERROR_MESSAGES.get(
        type(exc), "Unexpected http response " + str(exc)
    )
    raise BraintreeException(msg)
