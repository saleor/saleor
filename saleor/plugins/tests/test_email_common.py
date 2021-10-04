import pytest
from django.core.exceptions import ValidationError

from saleor.plugins.email_common import validate_default_email_configuration


@pytest.mark.parametrize(
    "email",
    (
        "this_is_not_an_email",
        "@",
        ".@.test",
        "almost_correct_email@",
    ),
)
def test_validate_default_email_configuration_bad_email(
    email, plugin_configuration, email_configuration
):
    email_configuration["sender_address"] = email

    with pytest.raises(ValidationError):
        validate_default_email_configuration(plugin_configuration, email_configuration)


def test_validate_default_email_configuration_correct_email(
    plugin_configuration, email_configuration
):
    email_configuration["sender_address"] = "this_is@correct.email"
    validate_default_email_configuration(plugin_configuration, email_configuration)
