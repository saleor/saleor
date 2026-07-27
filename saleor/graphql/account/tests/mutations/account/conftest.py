from unittest import mock

import pytest

REQUEST_EMAIL_CHANGE_QUERY = """
mutation requestEmailChange(
    $password: String!, $new_email: String!, $redirect_url: String!, $channel:String
) {
    requestEmailChange(
        password: $password,
        newEmail: $new_email,
        redirectUrl: $redirect_url,
        channel: $channel
    ) {
        user {
            email
        }
        errors {
            code
            message
            field
        }
  }
}
"""

CONFIRM_EMAIL_UPDATE_QUERY = """
mutation emailUpdate($token: String!, $channel: String) {
    confirmEmailChange(token: $token, channel: $channel){
        user {
            email
        }
        errors {
            code
            message
            field
        }
  }
}
"""


@pytest.fixture
def throttling_disabled():
    """Disable password throttling."""

    with mock.patch("saleor.account.throttling.cache"):
        yield
