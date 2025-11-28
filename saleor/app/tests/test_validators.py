import pytest
from django.core.exceptions import ValidationError

from ... import __version__
from ...app.validators import (
    AppExtensionOptions,
    AppURLValidator,
)
from ..error_codes import AppErrorCode
from ..manifest_validations import (
    _clean_author,
    _clean_extension_url,
    _clean_extensions,
    _clean_required_saleor_version,
    _parse_version,
)
from ..types import AppExtensionTarget
from ..validators import brand_validator


def test_validate_url():
    url_validator = AppURLValidator()
    url = "http://otherapp:3000"
    assert url_validator(url) is None


def test_validate_invalid_url():
    url_validator = AppURLValidator()
    url = "otherapp:3000"
    with pytest.raises(ValidationError):
        url_validator(url)


def test_parse_version():
    assert str(_parse_version(__version__)) == __version__


@pytest.mark.parametrize(
    ("required_version", "version", "satisfied"),
    [
        ("*", "3.12.1", True),
        ("3.8 - 3.9 || ~3.10.2 || 3.11.* || 3.12.x", "3.12.1", True),
        ("^3.12.0-0 <=3.14", "3.12.0-a", True),
        ("^3.12", "4.0.0", False),
        ("^3.12", "3.12.0-a", False),
        ("^3.12", "3.13.0-a", True),
    ],
)
def test_clean_required_saleor_version(required_version, version, satisfied):
    cleaned = _clean_required_saleor_version(required_version, False, version)
    assert cleaned == {"constraint": required_version, "satisfied": satisfied}


def test_clean_required_saleor_version_optional():
    assert _clean_required_saleor_version(None, False) is None


@pytest.mark.parametrize(
    "required_version", ["3.8-3.9", "^3w.11", {"wrong", "data type"}, 3, 3.12]
)
def test_clean_required_saleor_version_with_invalid_range(required_version):
    with pytest.raises(ValidationError) as error:
        _clean_required_saleor_version(required_version, False, "3.12.1")
    assert error.value.code == AppErrorCode.INVALID.value


def test_clean_required_saleor_version_raise_for_saleor_version():
    with pytest.raises(ValidationError) as error:
        _clean_required_saleor_version("^3.13", True, "3.12.1")
    assert error.value.code == AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value


@pytest.mark.parametrize(
    ("author", "cleaned"), [(None, None), (" Acme Ltd ", "Acme Ltd")]
)
def test_clean_author(author, cleaned):
    assert _clean_author(author) == cleaned


def test_brand_validator_required_fields():
    with pytest.raises(ValidationError) as error:
        brand_validator({"logo": {}})
    assert error.value.code == AppErrorCode.REQUIRED.value


@pytest.mark.parametrize(
    "url",
    [
        "example.com/logo.png",
        "https://exmple.com/logo",
        "https://exmple.com/logo.jpg",
    ],
)
def test_brand_validator_with_invalid_logo_url(url):
    with pytest.raises(ValidationError) as error:
        brand_validator({"logo": {"default": url}})
    assert error.value.code == AppErrorCode.INVALID_URL_FORMAT.value


def test_clean_extensions_new_tab_valid_relative_url(app_manifest):
    app_manifest["appUrl"] = "https://app.example.com"
    extension = {
        "url": "/relative/path",
        "target": AppExtensionTarget.NEW_TAB,
    }

    _clean_extension_url(extension, app_manifest)


@pytest.mark.parametrize(
    ("extension", "manifest", "should_raise"),
    [
        # url starts with /, target APP_PAGE, appUrl provided
        (
            {"url": "/page", "target": AppExtensionTarget.APP_PAGE},
            {
                "tokenTargetUrl": "https://app.example.com",
                "appUrl": "https://app.example.com",
            },
            False,
        ),
        # url starts with /, target NEW_TAB, should not raise
        (
            {"url": "/tab", "target": AppExtensionTarget.NEW_TAB},
            {
                "tokenTargetUrl": "https://app.example.com",
                "appUrl": "https://app.example.com",
            },
            False,
        ),
        # url starts with protocol, target APP_PAGE, should raise
        (
            {
                "url": "https://app.example.com/page",
                "target": AppExtensionTarget.APP_PAGE,
            },
            {"tokenTargetUrl": "https://app.example.com"},
            True,
        ),
        # url starts with protocol, target NEW_TAB, method POST, valid host
        (
            {
                "url": "https://app.example.com/page",
                "target": AppExtensionTarget.NEW_TAB,
                "options": {"newTabTarget": {"method": "POST"}},
            },
            {"tokenTargetUrl": "https://app.example.com"},
            False,
        ),
        # url starts with protocol, target NEW_TAB, method POST, invalid host
        (
            {
                "url": "https://other.com/page",
                "target": AppExtensionTarget.NEW_TAB,
                "options": {"newTabTarget": {"method": "POST"}},
            },
            {"tokenTargetUrl": "https://app.example.com"},
            True,
        ),
        # url is valid absolute, target POPUP
        (
            {"url": "https://app.example.com/page", "target": AppExtensionTarget.POPUP},
            {"tokenTargetUrl": "https://app.example.com"},
            False,
        ),
    ],
)
def test_clean_extension_url(extension, manifest, should_raise):
    if should_raise:
        with pytest.raises(ValidationError):
            _clean_extension_url(extension, manifest)

    else:
        _clean_extension_url(extension, manifest)


def test_new_tab_relative_url_without_app_url(app_manifest):
    # given
    app_manifest["appUrl"] = None

    extension = {
        "url": "/relative/path",
        "target": AppExtensionTarget.NEW_TAB,
    }

    app_manifest["extensions"] = [extension]

    # when & then
    with pytest.raises(ValidationError):
        _clean_extension_url(extension, manifest_data=app_manifest)


def test_clean_extension_url_https_only(settings):
    # given
    settings.ENABLE_SSL = True

    # when & then
    with pytest.raises(ValidationError):
        _clean_extension_url(
            {
                "url": "http://app.example.com/page",
                "target": AppExtensionTarget.NEW_TAB,
                "options": {"newTabTarget": {"method": "POST"}},
            },
            {
                "tokenTargetUrl": "https://app.example.com",
                "appUrl": "https://app.example.com",
            },
        )


def test_clean_extension_url_http_if_SSL_disabled(settings):
    # given
    settings.ENABLE_SSL = False

    # when
    result = _clean_extension_url(
        {"url": "http://app.example.com/page", "target": AppExtensionTarget.NEW_TAB},
        {
            "tokenTargetUrl": "https://app.example.com",
            "appUrl": "https://app.example.com",
        },
    )

    # then
    assert result is None


def test_app_extension_options_accepts_only_one():
    # Given
    parsed = AppExtensionOptions().model_validate({"widgetTarget": {"method": "GET"}})

    assert parsed.new_tab_target is None
    assert parsed.widget_target is not None

    parsed = AppExtensionOptions().model_validate({"newTabTarget": {"method": "GET"}})

    assert parsed.new_tab_target is not None
    assert parsed.widget_target is None

    with pytest.raises(
        ValueError, match="Only one of 'newTabTarget' or 'widgetTarget' can be set."
    ):
        AppExtensionOptions.model_validate(
            {
                "newTabTarget": {"method": "GET"},
                "widgetTarget": {"method": "GET"},
            }
        )

    # when
    parsed = AppExtensionOptions().model_validate({})

    # then
    assert parsed.new_tab_target is None
    assert parsed.widget_target is None


@pytest.mark.parametrize(
    ("app_url", "extension_url", "should_raise"),
    [
        (None, "/some-path", True),  # Test missing token_target_url
        ("https://example.com", "/some-path", False),  # Test valid token_target_url
    ],
)
def test_clean_extension_url_token_target_url(app_url, extension_url, should_raise):
    # Given
    extension = {"url": extension_url, "target": "APP_PAGE"}
    manifest_data = {"tokenTargetUrl": app_url, "appUrl": "https://example.com"}

    # When & Then
    if should_raise:
        with pytest.raises(ValidationError, match="token_target_url is missing"):
            _clean_extension_url(extension, manifest_data)
    else:
        # Should not raise ValidationError
        _clean_extension_url(extension, manifest_data)


@pytest.mark.parametrize(
    "mount",
    [
        "ORDER_DETAILS_WIDGETS",
        "PRODUCT_DETAILS_WIDGETS",
        "VOUCHER_DETAILS_WIDGETS",
        "DRAFT_ORDER_DETAILS_WIDGETS",
        "GIFT_CARD_DETAILS_WIDGETS",
        "CUSTOMER_DETAILS_WIDGETS",
        "COLLECTION_DETAILS_WIDGETS",
    ],
)
def test_widget_target_available_mounts_valid(mount, app_manifest):
    # Given
    extension = {
        "target": "WIDGET",
        "mount": mount,
        "url": "https://example.com/widget",
        "label": "label",
    }
    errors = {"extensions": []}

    app_manifest["extensions"] = [extension]

    # When
    _clean_extensions(app_manifest, [], errors)

    # Then
    assert len(errors["extensions"]) == 0


@pytest.mark.parametrize(
    "mount",
    ["CATEGORY_OVERVIEW_CREATECATEGORY_OVERVIEW_MORE_ACTIONS"],
)
def test_widget_target_available_mounts_invalid(mount, app_manifest):
    # Given
    extension = {
        "target": "WIDGET",
        "mount": mount,
        "url": "https://example.com/widget",
        "label": "label",
    }
    errors = {"extensions": []}

    app_manifest["extensions"] = [extension]

    # When
    _clean_extensions(app_manifest, [], errors)

    # Then
    assert "extensions" in errors
