import base64

from ..shipping_helpers import convert_to_app_id_with_identifier


def test_convert_to_app_id_with_identifier_valid(app):
    # given
    method_id = "123"
    shipping_app_id = base64.b64encode(str.encode(f"app:{app.pk}:{method_id}")).decode(
        "utf-8"
    )

    # when
    app_id_with_identifier = convert_to_app_id_with_identifier(shipping_app_id)

    # then
    assert app_id_with_identifier
    assert (
        base64.b64decode(app_id_with_identifier).decode()
        == f"app:{app.identifier}:{method_id}"
    )


def test_convert_to_app_id_with_identifier_missing_shipping_id(app):
    # given
    shipping_app_id = base64.b64encode(str.encode(f"app:{app.pk}")).decode("utf-8")

    # when
    app_id_with_identifier = convert_to_app_id_with_identifier(shipping_app_id)

    # then
    assert app_id_with_identifier is None


def test_convert_to_app_id_with_identifier_missing_app_for_given_id():
    # given
    method_id = "123"
    app_id = 321
    shipping_app_id = base64.b64encode(str.encode(f"app:{app_id}:{method_id}")).decode(
        "utf-8"
    )

    # when
    app_id_with_identifier = convert_to_app_id_with_identifier(shipping_app_id)

    # then
    assert app_id_with_identifier is None


def test_convert_to_app_id_with_identifier_invalid_app_id():
    # given
    method_id = "123"
    app_id = "xyz"
    shipping_app_id = base64.b64encode(str.encode(f"app:{app_id}:{method_id}")).decode(
        "utf-8"
    )

    # when
    app_id_with_identifier = convert_to_app_id_with_identifier(shipping_app_id)

    # then
    assert app_id_with_identifier is None
