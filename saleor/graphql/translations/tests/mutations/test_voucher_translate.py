import graphene
import pytest

from .....core.error_codes import TranslationErrorCode
from ....core.enums import LanguageCodeEnum
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VOUCHER_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation (
        $id: ID,
        $externalReference: String,
        $languageCode: LanguageCodeEnum!,
        $input: NameTranslationInput!
    ) {
        voucherTranslate(
            id: $id,
            externalReference: $externalReference,
            languageCode: $languageCode,
            input: $input
        ) {
            voucher {
                externalReference
                translation(languageCode: $languageCode) {
                    name
                    language {
                        code
                    }
                }
            }
            errors {
                message
                code
                field
            }
        }
    }
"""


def test_by_external_reference(
    staff_api_client, voucher, permission_manage_translations, mocker
):
    # given
    external_reference = "voucher-ext-ref"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish voucher"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["voucherTranslate"]
    assert data["errors"] == []
    assert data["voucher"] == {
        "externalReference": external_reference,
        "translation": {
            "name": name,
            "language": {"code": language_code.name},
        },
    }
    translation = voucher.translations.get(language_code=language_code.value)
    assert translation.name == name
    mocked_translations_created.assert_called_once_with([translation])


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            "id",
            TranslationErrorCode.REQUIRED,
            "This field is required",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            "id",
            TranslationErrorCode.REQUIRED,
            "This field is required",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            TranslationErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            TranslationErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'externalReference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            TranslationErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    voucher,
    permission_manage_translations,
    mocker,
):
    # given
    voucher.external_reference = "existing-reference"
    voucher.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Voucher", voucher.pk)
    variables["languageCode"] = LanguageCodeEnum.PL.name
    variables["input"] = {"name": "Polish voucher"}

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["voucherTranslate"]
    assert data["voucher"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert voucher.translations.exists() is False
    mocked_translations_created.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", None, False),
        ("customer", "user_api_client", None, False),
        ("staff_without_permission", "staff_api_client", None, False),
        (
            "staff_with_permission",
            "staff_api_client",
            "permission_manage_translations",
            True,
        ),
        ("app_without_permission", "app_api_client", None, False),
        (
            "app_with_permission",
            "app_api_client",
            "permission_manage_translations",
            True,
        ),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    request,
    voucher,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        permission = request.getfixturevalue(permission_fixture)
        if client.app:
            client.app.permissions.add(permission)
        else:
            client.user.user_permissions.add(permission)
    external_reference = "existing-reference"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish voucher"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = client.post_graphql(
        VOUCHER_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherTranslate"]
        assert data["errors"] == []
        assert data["voucher"]["translation"]["name"] == name
        translation = voucher.translations.get(language_code=language_code.value)
        assert translation.name == name
        mocked_translations_created.assert_called_once_with([translation])
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherTranslate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherTranslate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_TRANSLATIONS"
        )
        assert voucher.translations.exists() is False
        mocked_translations_created.assert_not_called()
