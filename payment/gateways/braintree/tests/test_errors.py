import pytest
from braintree.exceptions.authentication_error import AuthenticationError
from braintree.exceptions.authorization_error import AuthorizationError
from braintree.exceptions.gateway_timeout_error import GatewayTimeoutError
from braintree.exceptions.not_found_error import NotFoundError
from braintree.exceptions.request_timeout_error import RequestTimeoutError
from braintree.exceptions.server_error import ServerError
from braintree.exceptions.service_unavailable_error import ServiceUnavailableError
from braintree.exceptions.too_many_requests_error import TooManyRequestsError
from braintree.exceptions.upgrade_required_error import UpgradeRequiredError
from django.core.exceptions import ValidationError

from saleor.payment.gateways.braintree import BraintreeException, handle_braintree_error


@pytest.mark.parametrize(
    "braintree_error",
    [
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        RequestTimeoutError,
        UpgradeRequiredError,
        TooManyRequestsError,
        ServerError,
        ServiceUnavailableError,
        GatewayTimeoutError,
        ValidationError,  # ensure that we can handle all type of errors
    ],
)
def test_handle_braintree_error(braintree_error):
    with pytest.raises(BraintreeException):
        handle_braintree_error(braintree_error("Message"))
