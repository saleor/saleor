import json
from unittest.mock import ANY, patch

import pytest
from django.core.exceptions import ValidationError

from ...order.notifications import get_image_payload
from ..email_common import (
    DEFAULT_EMAIL_CONFIGURATION,
    EmailConfig,
    get_plain_text_message_for_email,
    get_product_image_thumbnail,
    send_email,
    validate_default_email_configuration,
)
from ..error_codes import PluginErrorCode


@pytest.mark.parametrize(
    "email",
    [
        "this_is_not_an_email",
        "@",
        ".@.test",
        "almost_correct_email@",
    ],
)
def test_validate_default_email_configuration_bad_email(
    email, plugin_configuration, email_configuration
):
    email_configuration["sender_address"] = email

    with pytest.raises(ValidationError) as e:
        validate_default_email_configuration(plugin_configuration, email_configuration)

    assert "sender_address" in e.value.args[0]
    assert e.value.args[0]["sender_address"].code == PluginErrorCode.INVALID.value


@patch("saleor.plugins.email_common.validate_email_config")
def test_validate_default_email_configuration_correct_email(
    mock_email_config, plugin_configuration, email_configuration
):
    email_configuration["sender_address"] = "this_is@correct.email"
    validate_default_email_configuration(plugin_configuration, email_configuration)


@patch("saleor.plugins.email_common.validate_email_config")
def test_validate_default_email_configuration_backend_raises(
    validate_email_config_mock, plugin_configuration, email_configuration
):
    validate_email_config_mock.side_effect = Exception("[Errno 61] Connection refused")
    email_configuration["sender_address"] = "this_is@correct.email"

    with pytest.raises(ValidationError) as e:
        validate_default_email_configuration(plugin_configuration, email_configuration)

    expected_keys = [item["name"] for item in DEFAULT_EMAIL_CONFIGURATION]
    assert list(e.value.error_dict.keys()) == expected_keys

    for message in e.value.messages:
        assert message == (
            "Unable to connect to email backend."
            " Make sure that you provided correct values."
            " [Errno 61] Connection refused"
        )


@pytest.mark.parametrize(
    ("config", "expected_fields"),
    [
        ({"host": ""}, ["host"]),
        ({"port": ""}, ["port"]),
        ({"sender_address": ""}, ["sender_address"]),
        (
            {"host": "", "port": "", "sender_address": ""},
            ["host", "port", "sender_address"],
        ),
        ({"host": None}, ["host"]),
        ({"port": None}, ["port"]),
        ({"sender_address": None}, ["sender_address"]),
        (
            {"host": None, "port": None, "sender_address": None},
            ["host", "port", "sender_address"],
        ),
    ],
)
def test_validate_default_email_configuration_missing_smtp_values(
    config, expected_fields, plugin_configuration, email_configuration
):
    email_configuration.update(config)

    with pytest.raises(ValidationError) as e:
        validate_default_email_configuration(plugin_configuration, email_configuration)

    assert list(e.value.error_dict.keys()) == expected_fields


def test_get_product_image_thumbnail(product_with_image):
    # given
    image_data = {"original": get_image_payload(product_with_image.media.first())}

    # when
    thumbnail = get_product_image_thumbnail(None, 100, image_data)

    # then
    assert thumbnail == image_data["original"]["128"]


def test_get_product_image_thumbnail_simulate_json_dump_and_load(product_with_image):
    # given
    image_data = {"original": get_image_payload(product_with_image.media.first())}
    image_data = json.dumps(image_data)
    image_data = json.loads(image_data)
    # when
    thumbnail = get_product_image_thumbnail(None, 100, image_data)

    # then
    assert thumbnail == image_data["original"]["128"]


def test_get_product_image_thumbnail_image_missing(product_with_image):
    # given
    image_data = None

    # when
    thumbnail = get_product_image_thumbnail(None, 100, image_data)

    # then
    assert thumbnail is None


@pytest.mark.parametrize(
    ("html_message", "expected_output"),
    [
        (
            "<html><head>"
            '<style type="text/css">#outlook a { padding:0; }body { margin:0;padding:0;'
            "-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%; }table, td { "
            "border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt; }img "
            "{ border:0;height:auto;line-height:100%; outline:none;text-decoration:"
            "none;-ms-interpolation-mode:bicubic; }p { display:block;margin:13px 0; }"
            "</style></head><body><p>Hello World!</p></body></html>",
            "Hello World!",
        ),
        ("<p>Hello World!</p>", "Hello World!"),
        ("<html>Hello World!</html>", "Hello World!"),
        ("", ""),
        ("Hello World!", "Hello World!"),
    ],
)
def test_get_plain_text_message_for_email(html_message, expected_output):
    # when
    output = get_plain_text_message_for_email(
        html_message,
    )

    # then
    assert output == expected_output


@patch(
    "saleor.plugins.email_common.get_plain_text_message_for_email",
    wraps=get_plain_text_message_for_email,
)
@patch("saleor.plugins.email_common.send_mail")
def test_send_email(mocked_send_mail, mocked_get_plain_text):
    # given
    sender_address = "dummy@localhost.com"
    sender_name = "dummy"
    config = EmailConfig(sender_name=sender_name, sender_address=sender_address)
    recipment_list = ["dummy2@localhost.com"]

    email_content = "<html>Hello World!</html>"
    email_plain_text = "Hello World!"
    email_subject = "Email subject"

    # when
    send_email(config, recipment_list, "", email_subject, email_content)

    # then
    mocked_get_plain_text.assert_called_once_with(email_content)
    mocked_send_mail.assert_called_once_with(
        email_subject,
        email_plain_text,
        f"{sender_name} <{sender_address}>",
        recipment_list,
        html_message=email_content,
        connection=ANY,
    )
