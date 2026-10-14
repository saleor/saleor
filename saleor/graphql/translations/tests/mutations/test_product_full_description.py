import json

import graphene
import pytest
from django.db import connections
from django.test.utils import CaptureQueriesContext

from .....tests.utils import dummy_editorjs
from ....core.enums import (
    LanguageCodeEnum,
    ProductTranslateErrorCode,
    TranslationErrorCode,
)
from ....tests.utils import get_graphql_content
from .test_product_bulk_translate import PRODUCT_BULK_TRANSLATE_MUTATION
from .test_product_translate import PRODUCT_TRANSLATE_MUTATION


@pytest.mark.parametrize(
    "full_description",
    [dummy_editorjs("Unsupported full description", True), json.dumps({}), None],
)
@pytest.mark.parametrize("existing", [False, True])
def test_single_product_translation_rejects_full_description(
    request,
    staff_api_client,
    product,
    permission_manage_translations,
    full_description,
    existing,
):
    # given
    previous_name = None
    if existing:
        translation = request.getfixturevalue("product_translation_fr")
        previous_name = translation.name
    variables = {
        "id": graphene.Node.to_global_id("Product", product.pk),
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {"fullDescription": full_description, "name": "Must not be saved"},
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data == {
        "product": None,
        "errors": [
            {
                "field": "fullDescription",
                "code": TranslationErrorCode.INVALID.name,
                "message": "Full descriptions are only supported for categories and collections.",
            }
        ],
    }
    assert product.translations.count() == int(existing)
    if existing:
        translation.refresh_from_db()
        assert translation.name == previous_name


@pytest.mark.parametrize(
    "full_description",
    [dummy_editorjs("Unsupported full description", True), json.dumps({}), None],
)
@pytest.mark.parametrize("existing", [False, True])
def test_bulk_product_translation_rejects_full_description(
    request,
    staff_api_client,
    product,
    permission_manage_translations,
    full_description,
    existing,
):
    # given
    previous_name = None
    if existing:
        translation = request.getfixturevalue("product_translation_fr")
        previous_name = translation.name
    variables = {
        "translations": [
            {
                "id": graphene.Node.to_global_id("Product", product.pk),
                "languageCode": LanguageCodeEnum.FR.name,
                "translationFields": {
                    "fullDescription": full_description,
                    "name": "Must not be saved",
                },
            }
        ]
    }

    # when
    with CaptureQueriesContext(connections["default"]) as queries:
        response = staff_api_client.post_graphql(
            PRODUCT_BULK_TRANSLATE_MUTATION,
            variables,
            permissions=[permission_manage_translations],
        )

    # then
    assert [
        query["sql"] for query in queries if 'FROM "product_product"' in query["sql"]
    ] == []
    data = get_graphql_content(response)["data"]["productBulkTranslate"]
    assert data == {
        "count": 0,
        "results": [
            {
                "translation": None,
                "errors": [
                    {
                        "path": "fullDescription",
                        "code": ProductTranslateErrorCode.INVALID.name,
                        "message": "Full descriptions are only supported for categories and collections.",
                    }
                ],
            }
        ],
    }
    assert product.translations.count() == int(existing)
    if existing:
        translation.refresh_from_db()
        assert translation.name == previous_name
