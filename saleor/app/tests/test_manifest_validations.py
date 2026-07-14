import pytest
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

from ..error_codes import AppErrorCode
from ..manifest_schema import (
    EXTENSION_IDENTIFIER_MAX_LENGTH,
    ICON_MIME_TYPES,
    ManifestExtensionSchema,
    ManifestSchema,
)
from ..manifest_validations import clean_manifest_data

MINIMAL_MANIFEST = {
    "id": "app.example",
    "name": "My App",
    "version": "1.0.0",
}


def test_manifest_schema_valid_minimal():
    # given / when
    schema = ManifestSchema.model_validate(MINIMAL_MANIFEST)

    # then
    assert schema.id == MINIMAL_MANIFEST["id"]
    assert schema.name == MINIMAL_MANIFEST["name"]
    assert schema.version == MINIMAL_MANIFEST["version"]


def test_manifest_schema_missing_required_fields():
    # given
    manifest_data = {}

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    error_fields = {e["loc"][0] for e in errors}
    assert "id" in error_fields
    assert "name" in error_fields
    assert "version" in error_fields


def test_manifest_schema_invalid_token_target_url():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "tokenTargetUrl": "not-a-valid-url",
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"][0] == "tokenTargetUrl"
    assert errors[0]["ctx"]["error_code"] == AppErrorCode.INVALID_URL_FORMAT.value


def test_manifest_schema_valid_token_target_url():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "tokenTargetUrl": "https://example.com/register",
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.token_target_url == "https://example.com/register"


def test_manifest_schema_invalid_author_empty_string():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "author": "   ",
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"][0] == "author"
    assert errors[0]["ctx"]["error_code"] == AppErrorCode.INVALID.value


def test_manifest_schema_valid_author_none():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "author": None,
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.author is None


def test_manifest_schema_valid_author_strips_whitespace():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "author": "  Acme Ltd  ",
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.author == "Acme Ltd"


def test_manifest_schema_brand_missing_logo_default():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "brand": {"logo": {}},
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    assert any(e["loc"][-1] == "default" for e in errors)


def test_manifest_schema_brand_invalid_url():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "brand": {"logo": {"default": "not-a-url"}},
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["ctx"]["error_code"] == AppErrorCode.INVALID_URL_FORMAT.value


def test_manifest_schema_brand_invalid_mime_type():
    # given
    assert "image/jpeg" not in ICON_MIME_TYPES
    manifest_data = {
        **MINIMAL_MANIFEST,
        "brand": {"logo": {"default": "https://example.com/logo.jpg"}},
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["ctx"]["error_code"] == AppErrorCode.INVALID_URL_FORMAT.value


def test_manifest_schema_brand_valid_png():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "brand": {"logo": {"default": "https://example.com/logo.png"}},
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.brand is not None
    assert schema.brand.logo.default == "https://example.com/logo.png"


def test_manifest_schema_extensions_null_defaults_to_empty_list():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": None,
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.extensions == []


def test_manifest_schema_webhooks_null_defaults_to_empty_list():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "webhooks": None,
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.webhooks == []


def test_manifest_schema_extension_missing_required_fields():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [{"url": "https://example.com/ext"}],
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    error_fields = {e["loc"][-1] for e in errors}
    assert "label" in error_fields
    assert "mount" in error_fields


def test_manifest_schema_webhook_missing_required_fields():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "webhooks": [{"name": "my-webhook"}],
    }

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestSchema.model_validate(manifest_data)

    # then
    errors = exc_info.value.errors()
    error_fields = {e["loc"][-1] for e in errors}
    assert "targetUrl" in error_fields
    assert "query" in error_fields


def test_manifest_schema_webhook_is_active_defaults_to_true():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "webhooks": [
            {
                "name": "my-webhook",
                "targetUrl": "https://example.com/webhook",
                "query": "subscription { event { ... on OrderCreated { order { id } } } }",
            }
        ],
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.webhooks[0].is_active is True


def test_manifest_schema_full_input():
    # given
    manifest_data = {
        "id": "app.example",
        "name": "My App",
        "version": "1.0.0",
        "tokenTargetUrl": "https://example.com/token",
        "appUrl": "https://example.com",
        "homepageUrl": "https://example.com",
        "supportUrl": "https://example.com/support",
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.token_target_url == manifest_data["tokenTargetUrl"]
    assert schema.app_url == manifest_data["appUrl"]
    assert schema.homepage_url == manifest_data["homepageUrl"]
    assert schema.support_url == manifest_data["supportUrl"]


def test_manifest_schema_extra_fields_ignored():
    # given
    manifest_data = {
        **MINIMAL_MANIFEST,
        "unknownField": "some value",
        "anotherExtra": 42,
    }

    # when
    schema = ManifestSchema.model_validate(manifest_data)

    # then
    assert schema.id == MINIMAL_MANIFEST["id"]


def _extension(label, identifier=None):
    extension = {
        "label": label,
        "url": "https://example.com/ext",
        "mount": "PRODUCT_OVERVIEW_MORE_ACTIONS",
        "target": "POPUP",
    }
    if identifier is not None:
        extension["identifier"] = identifier
    return extension


@pytest.mark.django_db
def test_clean_manifest_data_accepts_unique_extension_identifiers():
    # given - two extensions with distinct identifiers
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [
            _extension("First", identifier="first-ext"),
            _extension("Second", identifier="second-ext"),
        ],
    }

    # when
    clean_manifest_data(manifest_data)

    # then - identifiers are preserved on the cleaned manifest
    assert manifest_data["extensions"][0]["identifier"] == "first-ext"
    assert manifest_data["extensions"][1]["identifier"] == "second-ext"


@pytest.mark.django_db
def test_clean_manifest_data_rejects_duplicate_extension_identifiers():
    # given - two extensions reuse the same identifier within one manifest
    duplicate_identifier = "refund-button"
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [
            _extension("First", identifier=duplicate_identifier),
            _extension("Second", identifier=duplicate_identifier),
        ],
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        clean_manifest_data(manifest_data)

    # then
    extension_errors = exc_info.value.error_dict["extensions"]
    assert len(extension_errors) == 1
    error = extension_errors[0]
    assert error.code == AppErrorCode.DUPLICATED_EXTENSION_IDENTIFIER.value
    assert duplicate_identifier in error.message


@pytest.mark.django_db
def test_clean_manifest_data_allows_multiple_extensions_without_identifier():
    # given - several extensions omit the identifier entirely
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [
            _extension("First"),
            _extension("Second"),
        ],
    }

    # when
    clean_manifest_data(manifest_data)

    # then - absent identifiers are normalized to None and do not collide
    assert manifest_data["extensions"][0]["identifier"] is None
    assert manifest_data["extensions"][1]["identifier"] is None


@pytest.mark.django_db
def test_clean_manifest_data_coerces_blank_identifier_to_none():
    # given - blank and whitespace-only identifiers
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [
            _extension("First", identifier="   "),
            _extension("Second", identifier=""),
        ],
    }

    # when
    clean_manifest_data(manifest_data)

    # then - both are treated as not provided, so no duplicate error is raised
    assert manifest_data["extensions"][0]["identifier"] is None
    assert manifest_data["extensions"][1]["identifier"] is None


@pytest.mark.django_db
def test_clean_manifest_data_strips_surrounding_whitespace_from_identifier():
    # given - identifier padded with whitespace
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [_extension("First", identifier="  refund-button  ")],
    }

    # when
    clean_manifest_data(manifest_data)

    # then
    assert manifest_data["extensions"][0]["identifier"] == "refund-button"


@pytest.mark.django_db
def test_clean_manifest_data_accepts_identifier_at_max_length():
    # given - identifier exactly at the maximum allowed length
    identifier = "a" * EXTENSION_IDENTIFIER_MAX_LENGTH
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [_extension("First", identifier=identifier)],
    }

    # when
    clean_manifest_data(manifest_data)

    # then
    assert manifest_data["extensions"][0]["identifier"] == identifier


@pytest.mark.django_db
def test_clean_manifest_data_rejects_too_long_identifier():
    # given - identifier exceeding the maximum allowed length
    identifier = "a" * (EXTENSION_IDENTIFIER_MAX_LENGTH + 1)
    manifest_data = {
        **MINIMAL_MANIFEST,
        "extensions": [_extension("First", identifier=identifier)],
    }

    # when
    with pytest.raises(ValidationError) as exc_info:
        clean_manifest_data(manifest_data)

    # then
    expected_message = (
        f"Identifier is too long. Maximum length is "
        f"{EXTENSION_IDENTIFIER_MAX_LENGTH} characters."
    )
    extension_errors = exc_info.value.error_dict["extensions"]
    assert len(extension_errors) == 1
    error = extension_errors[0]
    assert error.code == AppErrorCode.INVALID.value
    assert error.message == expected_message


def test_manifest_extension_schema_rejects_too_long_identifier():
    # given - identifier exceeding the maximum allowed length
    identifier = "a" * (EXTENSION_IDENTIFIER_MAX_LENGTH + 1)
    extension_data = _extension("First", identifier=identifier)

    # when
    with pytest.raises(PydanticValidationError) as exc_info:
        ManifestExtensionSchema.model_validate(extension_data)

    # then
    expected_message = (
        f"Identifier is too long. Maximum length is "
        f"{EXTENSION_IDENTIFIER_MAX_LENGTH} characters."
    )
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("identifier",)
    assert errors[0]["msg"] == expected_message
    assert errors[0]["ctx"]["error_code"] == AppErrorCode.INVALID.value


def test_manifest_extension_schema_accepts_identifier_at_max_length():
    # given - identifier exactly at the maximum allowed length
    identifier = "a" * EXTENSION_IDENTIFIER_MAX_LENGTH
    extension_data = _extension("First", identifier=identifier)

    # when
    schema = ManifestExtensionSchema.model_validate(extension_data)

    # then
    assert schema.identifier == identifier


def test_manifest_schema_deprecated_fields_accepted():
    # given — deprecated fields are excluded from schema but must not cause a
    # validation error, and must remain accessible in the original dict so that
    # downstream code (installation_utils, app_fetch_manifest) can still read them
    data_privacy = "We do not store your data."
    configuration_url = "https://example.com/config"
    manifest_data = {
        **MINIMAL_MANIFEST,
        "dataPrivacy": data_privacy,
        "configurationUrl": configuration_url,
    }

    # when
    ManifestSchema.model_validate(manifest_data)

    # then — original dict is untouched; downstream readers can still access the values
    assert manifest_data["dataPrivacy"] == data_privacy
    assert manifest_data["configurationUrl"] == configuration_url
