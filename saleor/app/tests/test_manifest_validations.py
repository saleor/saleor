import pytest
from pydantic import ValidationError as PydanticValidationError

from ..error_codes import AppErrorCode
from ..manifest_schema import ManifestSchema

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
