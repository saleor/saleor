import graphene
import pytest

from .....core.error_codes import TranslationErrorCode
from .....product.models import ProductTranslation
from ....core.enums import LanguageCodeEnum
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

PRODUCT_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: TranslationInput!
    ) {
       productTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            product {
                translation(languageCode: $languageCode) {
                    name
                    slug
                    language {
                        code
                    }
                    __typename
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


def test_product_translate(
    staff_api_client,
    product,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Product", product.id)
    name = "Polish name"
    slug = "polish-name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "name": name,
            "slug": slug,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["slug"] == slug
    translation = product.translations.first()
    assert translation.name == name
    assert translation.slug == slug


def test_product_translate_without_slug(
    staff_api_client,
    product,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Product", product.id)
    name = "Polish name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] is None
    translation = product.translations.first()
    assert translation.name == name
    assert translation.slug is None


def test_product_translate_update(
    staff_api_client,
    product,
    product_translation_fr,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Product", product.id)
    name = "New french name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {
            "name": name,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    translation = product.translations.first()
    assert translation.name == name


def test_product_translate_update_when_slug_exists(
    staff_api_client,
    product,
    product_translation_fr,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Product", product.id)
    name = "New french name"
    slug = "french-name"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {
            "name": name,
        },
    }
    ProductTranslation.objects.filter(
        product=product, language_code=product_translation_fr.language_code
    ).update(slug=slug)

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productTranslate"]
    assert not data["errors"]
    translation_data = data["product"]["translation"]

    assert translation_data["name"] == name
    assert translation_data["slug"] == slug
    translation = product.translations.first()
    assert translation.name == name
    assert translation.slug == slug


PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation (
        $id: ID,
        $externalReference: String,
        $languageCode: LanguageCodeEnum!,
        $input: TranslationInput!
    ) {
        productTranslate(
            id: $id,
            externalReference: $externalReference,
            languageCode: $languageCode,
            input: $input
        ) {
            product {
                externalReference
                translation(languageCode: $languageCode) {
                    name
                    slug
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
    staff_api_client, product, permission_manage_translations, mocker
):
    # given
    external_reference = "product-ext-ref"
    product.external_reference = external_reference
    product.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish name"
    slug = "polish-name"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name, "slug": slug},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data["errors"] == []
    assert data["product"] == {
        "externalReference": external_reference,
        "translation": {
            "name": name,
            "slug": slug,
            "language": {"code": language_code.name},
        },
    }
    translation = product.translations.get(language_code=language_code.value)
    assert translation.name == name
    assert translation.slug == slug
    mocked_translations_created.assert_called_once_with([translation])


def test_by_id_with_empty_external_reference(
    staff_api_client, product, permission_manage_translations
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    language_code = LanguageCodeEnum.PL
    name = "Polish name"
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "externalReference": "",
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data["errors"] == []
    assert data["product"]["translation"]["name"] == name
    translation = product.translations.get(language_code=language_code.value)
    assert translation.name == name


def test_update_by_external_reference(
    staff_api_client,
    product,
    product_translation_fr,
    permission_manage_translations,
    mocker,
):
    # given
    external_reference = "product-ext-ref"
    product.external_reference = external_reference
    product.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_updated = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_updated"
    )
    name = "New french name"
    variables = {
        "externalReference": external_reference,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {"name": name},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data["errors"] == []
    assert data["product"]["translation"]["name"] == name
    product_translation_fr.refresh_from_db(fields=("name",))
    assert product_translation_fr.name == name
    mocked_translations_updated.assert_called_once_with([product_translation_fr])


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
    product,
    permission_manage_translations,
    mocker,
):
    # given
    product.external_reference = "existing-reference"
    product.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Product", product.pk)
    variables["languageCode"] = LanguageCodeEnum.PL.name
    variables["input"] = {"name": "Polish name"}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data["product"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert product.translations.exists() is False
    mocked_translations_created.assert_not_called()


def test_external_reference_of_other_model(
    staff_api_client, product, category, permission_manage_translations, mocker
):
    # given
    category_reference = "category-reference"
    category.external_reference = category_reference
    category.save(update_fields=["external_reference"])
    staff_api_client.user.user_permissions.add(permission_manage_translations)
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    variables = {
        "externalReference": category_reference,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"name": "Polish name"},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data["product"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": "externalReference",
        "code": TranslationErrorCode.NOT_FOUND.name,
        "message": f"Couldn't resolve to a node: {category_reference}",
    }
    assert product.translations.exists() is False
    assert category.translations.exists() is False
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
    product,
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
    product.external_reference = external_reference
    product.save(update_fields=["external_reference"])
    mocked_translations_created = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    language_code = LanguageCodeEnum.PL
    name = "Polish name"
    variables = {
        "externalReference": external_reference,
        "languageCode": language_code.name,
        "input": {"name": name},
    }

    # when
    response = client.post_graphql(
        PRODUCT_TRANSLATE_BY_EXTERNAL_REFERENCE_MUTATION, variables
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["productTranslate"]
        assert data["errors"] == []
        assert data["product"]["translation"]["name"] == name
        translation = product.translations.get(language_code=language_code.value)
        assert translation.name == name
        mocked_translations_created.assert_called_once_with([translation])
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"productTranslate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["productTranslate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_TRANSLATIONS"
        )
        assert product.translations.exists() is False
        mocked_translations_created.assert_not_called()
