import graphene

from .....page.models import PageTranslation
from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content

PAGE_TRANSLATE_MUTATION = """
    mutation (
        $id: ID!,
        $languageCode: LanguageCodeEnum!,
        $input: PageTranslationInput!
    ) {
       pageTranslate(
            id: $id,
            languageCode: $languageCode,
            input: $input
        ) {
            page {
                translation(languageCode: $languageCode) {
                    title
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


def test_page_translate(
    staff_api_client,
    page,
    permission_manage_translations,
):
    # given

    id = graphene.Node.to_global_id("Page", page.id)
    title = "Polish page title"
    slug = "polish-title"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "title": title,
            "slug": slug,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTranslate"]
    assert not data["errors"]
    translation_data = data["page"]["translation"]

    assert translation_data["title"] == title
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] == slug
    translation = page.translations.first()
    assert translation.title == title
    assert translation.slug == slug


def test_page_translate_without_slug(
    staff_api_client,
    page,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Page", page.id)
    title = "Polish page title"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "title": title,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTranslate"]
    assert not data["errors"]
    translation_data = data["page"]["translation"]

    assert translation_data["title"] == title
    assert translation_data["language"]["code"] == LanguageCodeEnum.PL.name
    assert translation_data["slug"] is None
    translation = page.translations.first()
    assert translation.title == title
    assert translation.slug is None


def test_page_translate_update(
    staff_api_client,
    page,
    page_translation_fr,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Page", page.id)
    title = "New french title"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {
            "title": title,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTranslate"]
    assert not data["errors"]
    translation_data = data["page"]["translation"]

    assert translation_data["title"] == title
    translation = page.translations.first()
    assert translation.title == title


def test_page_translate_update_when_slug_exists(
    staff_api_client,
    page,
    page_translation_fr,
    permission_manage_translations,
):
    # given
    id = graphene.Node.to_global_id("Page", page.id)
    title = "New french title"
    slug = "french-title"
    variables = {
        "id": id,
        "languageCode": LanguageCodeEnum.FR.name,
        "input": {
            "title": title,
        },
    }
    PageTranslation.objects.filter(
        page=page, language_code=page_translation_fr.language_code
    ).update(slug=slug)

    # when
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTranslate"]
    assert not data["errors"]
    translation_data = data["page"]["translation"]

    assert translation_data["title"] == title
    assert translation_data["slug"] == slug
    translation = page.translations.first()
    assert translation.title == title
    assert translation.slug == slug
