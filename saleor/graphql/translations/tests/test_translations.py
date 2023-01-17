import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from ....attribute.utils import associate_attribute_values_to_instance
from ....permission.models import Permission
from ....tests.utils import dummy_editorjs
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_translation_payload
from ...core.enums import LanguageCodeEnum
from ...tests.utils import assert_no_permission, get_graphql_content
from ..schema import TranslatableKinds


def test_product_translation(user_api_client, product, channel_USD):
    description = dummy_editorjs("test desription")
    product.translations.create(
        language_code="pl", name="Produkt", description=description
    )

    query = """
    query productById($productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            translation(languageCode: PL) {
                name
                description
                descriptionJson
                language {
                    code
                }
            }
        }
    }
    """

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = user_api_client.post_graphql(
        query, {"productId": product_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    translation_data = data["product"]["translation"]
    assert translation_data["name"] == "Produkt"
    assert translation_data["language"]["code"] == "PL"
    assert (
        translation_data["description"]
        == translation_data["descriptionJson"]
        == dummy_editorjs("test desription", json_format=True)
    )


def test_product_translation_without_description(user_api_client, product, channel_USD):
    product.translations.create(language_code="pl", name="Produkt")

    query = """
    query productById($productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            translation(languageCode: PL) {
                name
                description
                descriptionJson
                language {
                    code
                }
            }
        }
    }
    """

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = user_api_client.post_graphql(
        query, {"productId": product_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    translation_data = data["product"]["translation"]
    assert translation_data["name"] == "Produkt"
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["description"] is None
    assert translation_data["descriptionJson"] == "{}"


def test_product_translation_with_app(app_api_client, product, channel_USD):
    product.translations.create(language_code="pl", name="Produkt")

    query = """
    query productById($productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = app_api_client.post_graphql(
        query, {"productId": product_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    assert data["product"]["translation"]["name"] == "Produkt"
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_variant_translation(user_api_client, variant, channel_USD):
    variant.translations.create(language_code="pl", name="Wariant")

    query = """
    query productVariantById($productVariantId: ID!, $channel: String) {
        productVariant(id: $productVariantId, channel: $channel) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    product_variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    response = user_api_client.post_graphql(
        query, {"productVariantId": product_variant_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    assert data["productVariant"]["translation"]["name"] == "Wariant"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"


def test_collection_translation(user_api_client, published_collection, channel_USD):
    description = dummy_editorjs("test desription")
    published_collection.translations.create(
        language_code="pl", name="Kolekcja", description=description
    )

    query = """
    query collectionById($collectionId: ID!, $channel: String) {
        collection(id: $collectionId, channel: $channel) {
            translation(languageCode: PL) {
                name
                description
                descriptionJson
                language {
                    code
                }
            }
        }
    }
    """

    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    variables = {"collectionId": collection_id, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]

    translation_data = data["collection"]["translation"]
    assert translation_data["name"] == "Kolekcja"
    assert translation_data["language"]["code"] == "PL"
    assert (
        translation_data["description"]
        == translation_data["descriptionJson"]
        == dummy_editorjs("test desription", json_format=True)
    )


def test_collection_translation_without_description(
    user_api_client, published_collection, channel_USD
):
    published_collection.translations.create(language_code="pl", name="Kolekcja")

    query = """
    query collectionById($collectionId: ID!, $channel: String) {
        collection(id: $collectionId, channel: $channel) {
            translation(languageCode: PL) {
                name
                description
                descriptionJson
                language {
                    code
                }
            }
        }
    }
    """

    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    variables = {"collectionId": collection_id, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]

    translation_data = data["collection"]["translation"]
    assert translation_data["name"] == "Kolekcja"
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["description"] is None
    assert translation_data["descriptionJson"] == "{}"


def test_category_translation(user_api_client, category):
    description = dummy_editorjs("test description")
    category.translations.create(
        language_code="pl", name="Kategoria", description=description
    )

    query = """
    query categoryById($categoryId: ID!) {
        category(id: $categoryId) {
            translation(languageCode: PL) {
                name
                description
                descriptionJson
                language {
                    code
                }
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = user_api_client.post_graphql(query, {"categoryId": category_id})
    data = get_graphql_content(response)["data"]

    translation_data = data["category"]["translation"]
    assert translation_data["name"] == "Kategoria"
    assert translation_data["language"]["code"] == "PL"
    assert (
        translation_data["description"]
        == translation_data["descriptionJson"]
        == dummy_editorjs("test description", json_format=True)
    )


def test_category_translation_without_description(user_api_client, category):
    category.translations.create(language_code="pl", name="Kategoria")

    query = """
    query categoryById($categoryId: ID!) {
        category(id: $categoryId) {
            translation(languageCode: PL) {
                name
                description
                descriptionJson
                language {
                    code
                }
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = user_api_client.post_graphql(query, {"categoryId": category_id})
    data = get_graphql_content(response)["data"]

    translation_data = data["category"]["translation"]
    assert translation_data["name"] == "Kategoria"
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["description"] is None
    assert translation_data["descriptionJson"] == "{}"


def test_voucher_translation(staff_api_client, voucher, permission_manage_discounts):
    voucher.translations.create(language_code="pl", name="Bon")

    query = """
    query voucherById($voucherId: ID!) {
        voucher(id: $voucherId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    response = staff_api_client.post_graphql(
        query, {"voucherId": voucher_id}, permissions=[permission_manage_discounts]
    )
    data = get_graphql_content(response)["data"]

    assert data["voucher"]["translation"]["name"] == "Bon"
    assert data["voucher"]["translation"]["language"]["code"] == "PL"


def test_sale_translation(staff_api_client, sale, permission_manage_discounts):
    sale.translations.create(language_code="pl", name="Wyprz")

    query = """
    query saleById($saleId: ID!) {
        sale(id: $saleId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    response = staff_api_client.post_graphql(
        query, {"saleId": sale_id}, permissions=[permission_manage_discounts]
    )
    data = get_graphql_content(response)["data"]

    assert data["sale"]["translation"]["name"] == "Wyprz"
    assert data["sale"]["translation"]["language"]["code"] == "PL"


def test_page_translation(user_api_client, page):
    content = dummy_editorjs("test content")
    page.translations.create(language_code="pl", title="Strona", content=content)

    query = """
    query pageById($pageId: ID!) {
        page(id: $pageId) {
            translation(languageCode: PL) {
                title
                content
                contentJson
                language {
                    code
                }
            }
        }
    }
    """

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = user_api_client.post_graphql(query, {"pageId": page_id})
    data = get_graphql_content(response)["data"]

    translation_data = data["page"]["translation"]
    assert translation_data["title"] == "Strona"
    assert translation_data["language"]["code"] == "PL"
    assert (
        translation_data["content"]
        == translation_data["contentJson"]
        == dummy_editorjs("test content", json_format=True)
    )


def test_page_translation_without_content(user_api_client, page):
    page.translations.create(language_code="pl", title="Strona")

    query = """
    query pageById($pageId: ID!) {
        page(id: $pageId) {
            translation(languageCode: PL) {
                title
                content
                contentJson
                language {
                    code
                }
            }
        }
    }
    """

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = user_api_client.post_graphql(query, {"pageId": page_id})
    data = get_graphql_content(response)["data"]

    translation_data = data["page"]["translation"]
    assert translation_data["title"] == "Strona"
    assert translation_data["language"]["code"] == "PL"
    assert translation_data["content"] is None
    assert translation_data["contentJson"] == "{}"


def test_attribute_translation(user_api_client, color_attribute):
    color_attribute.translations.create(language_code="pl", name="Kolor")

    query = """
    query {
        attributes(first: 1) {
            edges {
                node {
                    translation(languageCode: PL) {
                        name
                        language {
                            code
                        }
                    }
                }
            }
        }
    }
    """

    response = user_api_client.post_graphql(query)
    data = get_graphql_content(response)["data"]

    attribute = data["attributes"]["edges"][0]["node"]
    assert attribute["translation"]["name"] == "Kolor"
    assert attribute["translation"]["language"]["code"] == "PL"


def test_attribute_value_translation(user_api_client, pink_attribute_value):
    pink_attribute_value.translations.create(
        language_code="pl", name="Różowy", rich_text=dummy_editorjs("Pink")
    )

    query = """
    query {
        attributes(first: 1) {
            edges {
                node {
                    choices(first: 10) {
                        edges {
                            node {
                                translation(languageCode: PL) {
                                    name
                                    richText
                                    language {
                                        code
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = user_api_client.post_graphql(
        query, {"attributeValueId": attribute_value_id}
    )
    data = get_graphql_content(response)["data"]

    attribute_value = data["attributes"]["edges"][0]["node"]["choices"]["edges"][-1][
        "node"
    ]
    assert attribute_value["translation"]["name"] == "Różowy"
    assert attribute_value["translation"]["richText"] == json.dumps(
        dummy_editorjs("Pink")
    )
    assert attribute_value["translation"]["language"]["code"] == "PL"


def test_shipping_method_translation(
    staff_api_client, shipping_method, permission_manage_shipping
):
    shipping_method.translations.create(language_code="pl", name="DHL Polska")

    query = """
    query shippingZoneById($shippingZoneId: ID!) {
        shippingZone(id: $shippingZoneId) {
            shippingMethods {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
    """

    shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_method.shipping_zone.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"shippingZoneId": shipping_zone_id},
        permissions=[permission_manage_shipping],
    )
    data = get_graphql_content(response)["data"]

    shipping_method = data["shippingZone"]["shippingMethods"][-1]
    assert shipping_method["translation"]["name"] == "DHL Polska"
    assert shipping_method["translation"]["language"]["code"] == "PL"


def test_menu_item_translation(user_api_client, menu_item):
    menu_item.translations.create(language_code="pl", name="Odnośnik 1")

    query = """
    query menuItemById($menuItemId: ID!) {
        menuItem(id: $menuItemId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)
    response = user_api_client.post_graphql(query, {"menuItemId": menu_item_id})
    data = get_graphql_content(response)["data"]

    assert data["menuItem"]["translation"]["name"] == "Odnośnik 1"
    assert data["menuItem"]["translation"]["language"]["code"] == "PL"


def test_shop_translation(user_api_client, site_settings):
    site_settings.translations.create(language_code="pl", header_text="Nagłówek")

    query = """
    query {
        shop {
            translation(languageCode: PL) {
                headerText
                language {
                    code
                }
            }
        }
    }
    """

    response = user_api_client.post_graphql(query)
    data = get_graphql_content(response)["data"]

    assert data["shop"]["translation"]["headerText"] == "Nagłówek"
    assert data["shop"]["translation"]["language"]["code"] == "PL"


def test_product_no_translation(user_api_client, product, channel_USD):
    query = """
    query productById($productId: ID!, $channel: String) {
        product(id: $productId, channel: $channel) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = user_api_client.post_graphql(
        query, {"productId": product_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    assert data["product"]["translation"] is None


def test_product_variant_no_translation(user_api_client, variant, channel_USD):
    query = """
    query productVariantById($productVariantId: ID!, $channel: String) {
        productVariant(id: $productVariantId, channel: $channel) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    product_variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    response = user_api_client.post_graphql(
        query, {"productVariantId": product_variant_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    assert data["productVariant"]["translation"] is None


def test_collection_no_translation(user_api_client, published_collection, channel_USD):
    query = """
    query collectionById($collectionId: ID!, $channel: String) {
        collection(id: $collectionId, channel: $channel) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    variables = {"collectionId": collection_id, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(query, variables)
    data = get_graphql_content(response)["data"]

    assert data["collection"]["translation"] is None


def test_category_no_translation(user_api_client, category):
    query = """
    query categoryById($categoryId: ID!) {
        category(id: $categoryId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = user_api_client.post_graphql(query, {"categoryId": category_id})
    data = get_graphql_content(response)["data"]

    assert data["category"]["translation"] is None


def test_voucher_no_translation(staff_api_client, voucher, permission_manage_discounts):
    query = """
    query voucherById($voucherId: ID!) {
        voucher(id: $voucherId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    response = staff_api_client.post_graphql(
        query, {"voucherId": voucher_id}, permissions=[permission_manage_discounts]
    )
    data = get_graphql_content(response)["data"]

    assert data["voucher"]["translation"] is None


def test_page_no_translation(user_api_client, page):
    query = """
    query pageById($pageId: ID!) {
        page(id: $pageId) {
            translation(languageCode: PL) {
                title
                language {
                    code
                }
            }
        }
    }
    """

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = user_api_client.post_graphql(query, {"pageId": page_id})
    data = get_graphql_content(response)["data"]

    assert data["page"]["translation"] is None


def test_attribute_no_translation(user_api_client, color_attribute):
    query = """
    query {
        attributes(first: 1) {
            edges {
                node {
                    translation(languageCode: PL) {
                        name
                        language {
                            code
                        }
                    }
                }
            }
        }
    }
    """

    response = user_api_client.post_graphql(query)
    data = get_graphql_content(response)["data"]

    attribute = data["attributes"]["edges"][0]["node"]
    assert attribute["translation"] is None


def test_attribute_value_no_translation(user_api_client, pink_attribute_value):
    query = """
    query {
        attributes(first: 1) {
            edges {
                node {
                    choices(first: 10) {
                        edges {
                            node {
                                translation(languageCode: PL) {
                                    name
                                    language {
                                        code
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = user_api_client.post_graphql(
        query, {"attributeValueId": attribute_value_id}
    )
    data = get_graphql_content(response)["data"]

    attribute_value = data["attributes"]["edges"][0]["node"]["choices"]["edges"][-1][
        "node"
    ]
    assert attribute_value["translation"] is None


def test_shipping_method_no_translation(
    staff_api_client, shipping_method, permission_manage_shipping
):
    query = """
    query shippingZoneById($shippingZoneId: ID!) {
        shippingZone(id: $shippingZoneId) {
            shippingMethods {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
    """

    shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_method.shipping_zone.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"shippingZoneId": shipping_zone_id},
        permissions=[permission_manage_shipping],
    )
    data = get_graphql_content(response)["data"]

    shipping_method = data["shippingZone"]["shippingMethods"][0]
    assert shipping_method["translation"] is None


def test_menu_item_no_translation(user_api_client, menu_item):
    query = """
    query menuItemById($menuItemId: ID!) {
        menuItem(id: $menuItemId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)
    response = user_api_client.post_graphql(query, {"menuItemId": menu_item_id})
    data = get_graphql_content(response)["data"]

    assert data["menuItem"]["translation"] is None


def test_shop_no_translation(user_api_client, site_settings):
    query = """
    query {
        shop {
            translation(languageCode: PL) {
                headerText
                language {
                    code
                }
            }
        }
    }
    """

    response = user_api_client.post_graphql(query)
    data = get_graphql_content(response)["data"]

    assert data["shop"]["translation"] is None


PRODUCT_TRANSLATE_MUTATION = """
    mutation productTranslate($productId: ID!, $input: TranslationInput!) {
        productTranslate(id: $productId, languageCode: PL, input: $input) {
            product {
                translation(languageCode: PL) {
                    name
                    description
                    language {
                        code
                    }
                }
            }
            errors {
                field
                code
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        {"productId": product_id, "input": {"name": "Produkt PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] == "Produkt PL"
    assert data["product"]["translation"]["language"]["code"] == "PL"

    translation = product.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_product_create_translation_for_description(
    staff_api_client, product, permission_manage_translations
):
    product_id = graphene.Node.to_global_id("Product", product.id)
    description = dummy_editorjs("description", True)
    variables = {"productId": product_id, "input": {"description": description}}
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] is None
    assert data["product"]["translation"]["description"] == description
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_create_translation_for_description_and_name_as_null(
    staff_api_client, product, permission_manage_translations
):
    product_id = graphene.Node.to_global_id("Product", product.id)
    description = dummy_editorjs("description", True)
    variables = {
        "productId": product_id,
        "input": {"description": description, "name": None},
    }
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] is None
    assert data["product"]["translation"]["description"] == description
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_create_translation_with_app(
    app_api_client, product, permission_manage_translations
):
    product_id = graphene.Node.to_global_id("Product", product.id)
    response = app_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        {"productId": product_id, "input": {"name": "Produkt PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] == "Produkt PL"
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_create_translation_by_translatable_content_id(
    staff_api_client, product, permission_manage_translations
):
    translatable_content_id = graphene.Node.to_global_id(
        "ProductTranslatableContent", product.id
    )
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        {"productId": translatable_content_id, "input": {"name": "Produkt PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]
    assert data["product"]["translation"]["name"] == "Produkt PL"
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_create_translation_validates_name_length(
    staff_api_client, product, permission_manage_translations
):
    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {
        "productId": product_id,
        "input": {"description": None, "name": "Long" * 100},
    }
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        variables,
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"] is None
    assert data["errors"] == [
        {"field": "name", "code": "INVALID"},
    ]


def test_product_create_translation_by_invalid_translatable_content_id(
    staff_api_client, product, permission_manage_translations
):
    translatable_content_id = (
        "UHJvZHVjdFRyYW5zbGF0YWJsZUNvbnRlbnQ6NDkxMyd8fERCTVN"
        "fUElQRS5SRUNFSVZFX01FU1NBR0UoQ0hSKDk4KXx8Q0hSKDk4KXx8Q"
        "0hSKDk4KSwxNSl8fA=="
    )

    # String decodes to
    # ProductTranslatableContent:4913'||
    # DBMS_PIPE.RECEIVE_MESSAGE(CHR(98)||CHR(98)||CHR(98),15)||
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        {"productId": translatable_content_id, "input": {"name": "Produkt PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]
    errors = data["errors"][0]
    assert errors["code"] == "INVALID"
    assert errors["field"] == "id"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = product.translations.create(language_code="pl", name="Produkt")

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = staff_api_client.post_graphql(
        PRODUCT_TRANSLATE_MUTATION,
        {"productId": product_id, "input": {"name": "Produkt PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] == "Produkt PL"
    assert data["product"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


PRODUCT_VARIANT_TRANSLATE_MUTATION = """
mutation productVariantTranslate(
    $productVariantId: ID!, $input: NameTranslationInput!
    ) {
    productVariantTranslate(
            id: $productVariantId, languageCode: PL,
            input: $input) {
        productVariant {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
        errors {
            field
            code
        }
    }
}
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    variant,
    channel_USD,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    product_variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_TRANSLATE_MUTATION,
        {"productVariantId": product_variant_id, "input": {"name": "Wariant PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productVariantTranslate"]

    assert data["productVariant"]["translation"]["name"] == "Wariant PL"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"

    translation = variant.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_product_variant_create_translation_by_translatable_content_id(
    staff_api_client,
    variant,
    channel_USD,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "ProductVariantTranslatableContent", variant.id
    )
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_TRANSLATE_MUTATION,
        {"productVariantId": translatable_content_id, "input": {"name": "Wariant PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productVariantTranslate"]
    assert data["productVariant"]["translation"]["name"] == "Wariant PL"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_product_variant_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    variant,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = variant.translations.create(language_code="pl", name="Wariant")

    product_variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_TRANSLATE_MUTATION,
        {"productVariantId": product_variant_id, "input": {"name": "Wariant PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productVariantTranslate"]

    assert data["productVariant"]["translation"]["name"] == "Wariant PL"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_product_variant_translation_mutation_validates_inputs_length(
    staff_api_client,
    variant,
    channel_USD,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "ProductVariantTranslatableContent", variant.id
    )
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_TRANSLATE_MUTATION,
        {
            "productVariantId": translatable_content_id,
            "input": {"name": "Wariant PL" * 100},
        },
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productVariantTranslate"]
    assert data["productVariant"] is None
    assert data["errors"] == [
        {
            "field": "name",
            "code": "INVALID",
        }
    ]


COLLECTION_TRANSLATE_MUTATION = """
mutation collectionTranslate($collectionId: ID!, $input: TranslationInput!) {
    collectionTranslate(
            id: $collectionId, languageCode: PL,
            input: $input) {
        collection {
            translation(languageCode: PL) {
                name
                description
                language {
                    code
                }
            }
        }
        errors {
            field
            code
        }
    }
}
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_collection_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    published_collection,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        {"collectionId": collection_id, "input": {"name": "Kolekcja PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"]["translation"]["name"] == "Kolekcja PL"
    assert data["collection"]["translation"]["language"]["code"] == "PL"

    translation = published_collection.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_collection_create_translation_by_translatable_content_id(
    staff_api_client,
    published_collection,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "CollectionTranslatableContent", published_collection.id
    )
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        {"collectionId": translatable_content_id, "input": {"name": "Kolekcja PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]
    assert data["collection"]["translation"]["name"] == "Kolekcja PL"
    assert data["collection"]["translation"]["language"]["code"] == "PL"


def test_collection_create_translation_for_description(
    staff_api_client, published_collection, permission_manage_translations
):
    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    description = dummy_editorjs("description", True)
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        {"collectionId": collection_id, "input": {"description": description}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"]["translation"]["name"] is None
    assert data["collection"]["translation"]["description"] == description
    assert data["collection"]["translation"]["language"]["code"] == "PL"


def test_collection_create_translation_for_description_name_as_null(
    staff_api_client, published_collection, permission_manage_translations
):
    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    description = dummy_editorjs("description", True)
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        {
            "collectionId": collection_id,
            "input": {"description": description, "name": None},
        },
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"]["translation"]["name"] is None
    assert data["collection"]["translation"]["description"] == description
    assert data["collection"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_collection_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    published_collection,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = published_collection.translations.create(
        language_code="pl", name="Kolekcja"
    )

    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        {"collectionId": collection_id, "input": {"name": "Kolekcja PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"]["translation"]["name"] == "Kolekcja PL"
    assert data["collection"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_collection_translation_mutation_validates_inputs_length(
    staff_api_client, published_collection, permission_manage_translations
):
    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)
    description = dummy_editorjs("description", True)
    response = staff_api_client.post_graphql(
        COLLECTION_TRANSLATE_MUTATION,
        {
            "collectionId": collection_id,
            "input": {"description": description, "name": "long" * 100},
        },
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"] is None
    assert data["errors"] == [{"field": "name", "code": "INVALID"}]


CATEGORY_TRANSLATE_MUTATION = """
mutation categoryTranslate($categoryId: ID!, $input: TranslationInput!) {
    categoryTranslate(
            id: $categoryId, languageCode: PL,
            input: $input) {
        category {
            translation(languageCode: PL) {
                name
                description
                language {
                    code
                }
            }
        }
    }
}
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_category_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    category,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        {"categoryId": category_id, "input": {"name": "Kategoria PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]

    assert data["category"]["translation"]["name"] == "Kategoria PL"
    assert data["category"]["translation"]["language"]["code"] == "PL"

    translation = category.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_category_create_translation_by_translatable_content_id(
    staff_api_client,
    category,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "CategoryTranslatableContent", category.id
    )
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        {"categoryId": translatable_content_id, "input": {"name": "Kategoria PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]
    assert data["category"]["translation"]["name"] == "Kategoria PL"
    assert data["category"]["translation"]["language"]["code"] == "PL"


def test_category_create_translation_for_description(
    staff_api_client, category, permission_manage_translations
):
    category_id = graphene.Node.to_global_id("Category", category.id)
    description = dummy_editorjs("description", True)
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        {"categoryId": category_id, "input": {"description": description}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]

    assert data["category"]["translation"]["name"] is None
    assert data["category"]["translation"]["description"] == description
    assert data["category"]["translation"]["language"]["code"] == "PL"


def test_category_create_translation_for_description_name_as_null(
    staff_api_client, category, permission_manage_translations
):
    category_id = graphene.Node.to_global_id("Category", category.id)
    description = dummy_editorjs("description", True)
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        {
            "categoryId": category_id,
            "input": {"name": None, "description": description},
        },
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]

    assert data["category"]["translation"]["name"] is None
    assert data["category"]["translation"]["description"] == description
    assert data["category"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_category_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    category,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = category.translations.create(language_code="pl", name="Kategoria")

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        CATEGORY_TRANSLATE_MUTATION,
        {"categoryId": category_id, "input": {"name": "Kategoria PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]

    assert data["category"]["translation"]["name"] == "Kategoria PL"
    assert data["category"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


VOUCHER_TRANSLATE_MUTATION = """
    mutation voucherTranslate($voucherId: ID!) {
        voucherTranslate(
                id: $voucherId, languageCode: PL,
                input: {name: "Bon PL"}) {
            voucher {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    response = staff_api_client.post_graphql(
        VOUCHER_TRANSLATE_MUTATION,
        {"voucherId": voucher_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["voucherTranslate"]

    assert data["voucher"]["translation"]["name"] == "Bon PL"
    assert data["voucher"]["translation"]["language"]["code"] == "PL"

    translation = voucher.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_voucher_create_translation_by_translatable_content_id(
    staff_api_client,
    voucher,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "VoucherTranslatableContent", voucher.id
    )
    response = staff_api_client.post_graphql(
        VOUCHER_TRANSLATE_MUTATION,
        {"voucherId": translatable_content_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["voucherTranslate"]
    assert data["voucher"]["translation"]["name"] == "Bon PL"
    assert data["voucher"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    translation = voucher.translations.create(language_code="pl", name="Kategoria")

    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    response = staff_api_client.post_graphql(
        VOUCHER_TRANSLATE_MUTATION,
        {"voucherId": voucher_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["voucherTranslate"]

    assert data["voucher"]["translation"]["name"] == "Bon PL"
    assert data["voucher"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


SALE_TRANSLATION_MUTATION = """
    mutation saleTranslate($saleId: ID!) {
        saleTranslate(
                id: $saleId, languageCode: PL,
                input: {name: "Wyprz PL"}) {
            sale {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    sale,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    response = staff_api_client.post_graphql(
        SALE_TRANSLATION_MUTATION,
        {"saleId": sale_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["saleTranslate"]

    assert data["sale"]["translation"]["name"] == "Wyprz PL"
    assert data["sale"]["translation"]["language"]["code"] == "PL"

    translation = sale.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_sale_create_translation_by_translatable_content_id(
    staff_api_client,
    sale,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "SaleTranslatableContent", sale.id
    )
    response = staff_api_client.post_graphql(
        SALE_TRANSLATION_MUTATION,
        {"saleId": translatable_content_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["saleTranslate"]
    assert data["sale"]["translation"]["name"] == "Wyprz PL"
    assert data["sale"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sale_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    sale,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = sale.translations.create(language_code="pl", name="Sale")

    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    response = staff_api_client.post_graphql(
        SALE_TRANSLATION_MUTATION,
        {"saleId": sale_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["saleTranslate"]

    assert data["sale"]["translation"]["name"] == "Wyprz PL"
    assert data["sale"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


PAGE_TRANSLATE_MUTATION = """
mutation pageTranslate($pageId: ID!, $input: PageTranslationInput!) {
    pageTranslate(
            id: $pageId, languageCode: PL,
            input: $input) {
        page {
            translation(languageCode: PL) {
                title
                content
                language {
                    code
                }
            }
        }
    }
}
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        {"pageId": page_id, "input": {"title": "Strona PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]

    assert data["page"]["translation"]["title"] == "Strona PL"
    assert data["page"]["translation"]["language"]["code"] == "PL"

    translation = page.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_page_create_translation_for_content(
    staff_api_client, page, permission_manage_translations
):
    page_id = graphene.Node.to_global_id("Page", page.id)
    content = dummy_editorjs("content", True)
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        {"pageId": page_id, "input": {"content": content}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]

    assert data["page"]["translation"]["title"] is None
    assert data["page"]["translation"]["content"] == content
    assert data["page"]["translation"]["language"]["code"] == "PL"


def test_page_create_translation_for_content_title_as_null(
    staff_api_client, page, permission_manage_translations
):
    page_id = graphene.Node.to_global_id("Page", page.id)
    content = dummy_editorjs("content", True)
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        {"pageId": page_id, "input": {"title": None, "content": content}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]

    assert data["page"]["translation"]["title"] is None
    assert data["page"]["translation"]["content"] == content
    assert data["page"]["translation"]["language"]["code"] == "PL"


def test_page_create_translation_by_translatable_content_id(
    staff_api_client,
    page,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "PageTranslatableContent", page.id
    )
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        {"pageId": translatable_content_id, "input": {"title": "Strona PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]
    assert data["page"]["translation"]["title"] == "Strona PL"
    assert data["page"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    translation = page.translations.create(language_code="pl", title="Strona")

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = staff_api_client.post_graphql(
        PAGE_TRANSLATE_MUTATION,
        {"pageId": page_id, "input": {"title": "Strona PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]

    assert data["page"]["translation"]["title"] == "Strona PL"
    assert data["page"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


ATTRIBUTE_TRANSLATE_MUTATION = """
    mutation attributeTranslate($attributeId: ID!) {
        attributeTranslate(
            id: $attributeId,
            languageCode: PL,
            input: {name: "Kolor PL"}
        ) {
            attribute {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_attribute_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_TRANSLATE_MUTATION,
        {"attributeId": attribute_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeTranslate"]

    assert data["attribute"]["translation"]["name"] == "Kolor PL"
    assert data["attribute"]["translation"]["language"]["code"] == "PL"

    translation = color_attribute.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_attribute_create_translation_by_translatable_content_id(
    staff_api_client,
    color_attribute,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "Attribute", color_attribute.id
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_TRANSLATE_MUTATION,
        {"attributeId": translatable_content_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeTranslate"]
    assert data["attribute"]["translation"]["name"] == "Kolor PL"
    assert data["attribute"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_attribute_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    color_attribute,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = color_attribute.translations.create(language_code="pl", name="Kolor")

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    response = staff_api_client.post_graphql(
        ATTRIBUTE_TRANSLATE_MUTATION,
        {"attributeId": attribute_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeTranslate"]

    assert data["attribute"]["translation"]["name"] == "Kolor PL"
    assert data["attribute"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


ATTRIBUTE_VALUE_TRANSLATE_MUTATION = """
    mutation attributeValueTranslate(
        $attributeValueId: ID!,
        $input: AttributeValueTranslationInput!
    ) {
        attributeValueTranslate(
            id: $attributeValueId,
            languageCode: PL,
            input: $input
        ) {
            attributeValue {
                translation(languageCode: PL) {
                    name
                    richText
                    plainText
                    language {
                        code
                    }
                }
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_attribute_value_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    pink_attribute_value,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {"attributeValueId": attribute_value_id, "input": {"name": "Róż PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]

    assert data["attributeValue"]["translation"]["name"] == "Róż PL"
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"

    translation = pink_attribute_value.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_rich_text_attribute_value_create_translation(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_base_text = "Nowy Opis"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"richText": expected_rich_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_base_text
    assert data["attributeValue"]["translation"]["richText"] == expected_rich_text


def test_plain_text_attribute_value_create_translation(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_text = "Nowy Opis"

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"plainText": expected_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_text
    assert data["attributeValue"]["translation"]["plainText"] == expected_text


def test_attribute_value_create_translation_by_translatable_content_id(
    staff_api_client, pink_attribute_value, permission_manage_translations
):
    translatable_content_id = graphene.Node.to_global_id(
        "AttributeValueTranslatableContent", pink_attribute_value.id
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {"attributeValueId": translatable_content_id, "input": {"name": "Róż PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["name"] == "Róż PL"
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_attribute_value_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    pink_attribute_value,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = pink_attribute_value.translations.create(
        language_code="pl", name="Różowy"
    )

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {"attributeValueId": attribute_value_id, "input": {"name": "Róż PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]

    assert data["attributeValue"]["translation"]["name"] == "Róż PL"
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_rich_text_attribute_value_update_translation_only_rich_text(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    base_text = "Base Text"
    rich_text = dummy_editorjs(base_text)
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value.translations.create(
        language_code="pl", name=base_text, rich_text=rich_text
    )
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_base_text = "Nowy Opis"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"richText": expected_rich_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_base_text
    assert data["attributeValue"]["translation"]["richText"] == expected_rich_text


def test_rich_text_attribute_value_update_translation_only_rich_text_long_text(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    base_text = "Base Text"
    rich_text = dummy_editorjs(base_text)
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value.translations.create(
        language_code="pl", name=base_text, rich_text=rich_text
    )
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_base_text = "Nowy Opis. " * 100
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"richText": expected_rich_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert (
        data["attributeValue"]["translation"]["name"] == expected_base_text[:99] + "…"
    )
    assert data["attributeValue"]["translation"]["richText"] == expected_rich_text


def test_rich_text_attribute_value_update_translation_only_rich_text_name_set_manually(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    base_text = "Base Text"
    rich_text = dummy_editorjs(base_text)
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value.translations.create(
        language_code="pl", name=base_text, rich_text=rich_text
    )
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_name = "Moja nazwa attrybutu"
    expected_base_text = "Nowy Opis"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"name": expected_name, "richText": expected_rich_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_name
    assert data["attributeValue"]["translation"]["richText"] == expected_rich_text


def test_rich_text_attribute_value_update_translation_only_rich_text_empty_name(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    base_text = "Base Text"
    rich_text = dummy_editorjs(base_text)
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value.translations.create(
        language_code="pl", name=base_text, rich_text=rich_text
    )
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_base_text = "Nowy Opis"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"name": "", "richText": expected_rich_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == ""
    assert data["attributeValue"]["translation"]["richText"] == expected_rich_text


def test_rich_text_attribute_value_update_translation_only_rich_text_name_null(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    base_text = "Base Text"
    rich_text = dummy_editorjs(base_text)
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value.translations.create(
        language_code="pl", name=base_text, rich_text=rich_text
    )
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_base_text = "Nowy Opis"
    expected_rich_text = json.dumps(dummy_editorjs(expected_base_text))

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"name": None, "richText": expected_rich_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_base_text
    assert data["attributeValue"]["translation"]["richText"] == expected_rich_text


def test_plain_text_attribute_value_update_translation_only_plain_text(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Jakiś bazowy opis"
    attribute_value.translations.create(language_code="pl", plain_text=text)
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_text = "Nowy Opis"

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"plainText": expected_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_text
    assert data["attributeValue"]["translation"]["plainText"] == expected_text


def test_plain_text_attribute_value_update_translation_only_plain_text_long_text(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Jakiś bazowy opis"
    attribute_value.translations.create(language_code="pl", plain_text=text)
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_base_text = "Nowy Opis. " * 100

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"plainText": expected_base_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert (
        data["attributeValue"]["translation"]["name"] == expected_base_text[:99] + "…"
    )
    assert data["attributeValue"]["translation"]["plainText"] == expected_base_text


def test_plain_text_attribute_value_update_translation_name_set_manually(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Jakiś bazowy opis"
    attribute_value.translations.create(language_code="pl", plain_text=text)
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_name = "Moja nazwa attrybutu"
    expected_text = "Nowy Opis"

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"name": expected_name, "plainText": expected_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_name
    assert data["attributeValue"]["translation"]["plainText"] == expected_text


def test_plain_text_attribute_value_update_translation_empty_name(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Jakiś bazowy opis"
    attribute_value.translations.create(language_code="pl", plain_text=text)
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_text = "Nowy Opis"

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"name": "", "plainText": expected_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == ""
    assert data["attributeValue"]["translation"]["plainText"] == expected_text


def test_plain_text_attribute_value_update_translation_name_null(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Jakiś bazowy opis"
    attribute_value.translations.create(language_code="pl", plain_text=text)
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", attribute_value.id
    )
    expected_text = "Nowy Opis"

    # when
    response = staff_api_client.post_graphql(
        ATTRIBUTE_VALUE_TRANSLATE_MUTATION,
        {
            "attributeValueId": attribute_value_id,
            "input": {"name": None, "plainText": expected_text},
        },
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"
    assert data["attributeValue"]["translation"]["name"] == expected_text
    assert data["attributeValue"]["translation"]["plainText"] == expected_text


SHIPPING_PRICE_TRANSLATE = """
    mutation shippingPriceTranslate(
        $shippingMethodId: ID!, $input: ShippingPriceTranslationInput!
    ) {
        shippingPriceTranslate(
            id: $shippingMethodId,
            languageCode: PL,
            input: $input
        ) {
            shippingMethod {
                translation(languageCode: PL) {
                    name
                    description
                    language {
                        code
                    }
                }
            }
            errors {
                message
                code
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shipping_method_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_method,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    description = dummy_editorjs("description", True)
    variables = {
        "shippingMethodId": shipping_method_id,
        "input": {"name": "DHL PL", "description": description},
    }
    response = staff_api_client.post_graphql(
        SHIPPING_PRICE_TRANSLATE,
        variables,
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shippingPriceTranslate"]

    assert data["shippingMethod"]["translation"]["name"] == "DHL PL"
    assert data["shippingMethod"]["translation"]["description"] == description
    assert data["shippingMethod"]["translation"]["language"]["code"] == "PL"

    translation = shipping_method.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_shipping_method_create_translation_by_translatable_content_id(
    staff_api_client,
    shipping_method,
    permission_manage_translations,
):
    translatable_content_id = graphene.Node.to_global_id(
        "ShippingMethodTranslatableContent", shipping_method.id
    )
    description = dummy_editorjs("description", True)
    variables = {
        "shippingMethodId": translatable_content_id,
        "input": {"name": "DHL PL", "description": description},
    }
    response = staff_api_client.post_graphql(
        SHIPPING_PRICE_TRANSLATE,
        variables,
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shippingPriceTranslate"]

    assert data["shippingMethod"]["translation"]["name"] == "DHL PL"
    assert data["shippingMethod"]["translation"]["description"] == description
    assert data["shippingMethod"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shipping_method_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_method,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = shipping_method.translations.create(language_code="pl", name="DHL")

    query = """
    mutation shippingPriceTranslate($shippingMethodId: ID!) {
        shippingPriceTranslate(
                id: $shippingMethodId, languageCode: PL,
                input: {name: "DHL PL"}) {
            shippingMethod {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
    """

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"shippingMethodId": shipping_method_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shippingPriceTranslate"]

    assert data["shippingMethod"]["translation"]["name"] == "DHL PL"
    assert data["shippingMethod"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


MENU_ITEM_TRANSLATE = """
    mutation menuItemTranslate($menuItemId: ID!) {
        menuItemTranslate(
            id: $menuItemId, languageCode: PL,
            input: {name: "Odnośnik PL"}
        ) {
            menuItem {
                translation(languageCode: PL) {
                    name
                    language {
                        code
                    }
                }
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_menu_item_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    menu_item,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = menu_item.translations.create(language_code="pl", name="Odnośnik")

    translatable_content_id = graphene.Node.to_global_id(
        "MenuItemTranslatableContent", menu_item.id
    )
    response = staff_api_client.post_graphql(
        MENU_ITEM_TRANSLATE,
        {"menuItemId": translatable_content_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["menuItemTranslate"]

    assert data["menuItem"]["translation"]["name"] == "Odnośnik PL"
    assert data["menuItem"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_menu_item_create_translation_by_translatable_content_id(
    staff_api_client,
    menu_item,
    permission_manage_translations,
):
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)
    response = staff_api_client.post_graphql(
        MENU_ITEM_TRANSLATE,
        {"menuItemId": menu_item_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["menuItemTranslate"]
    assert data["menuItem"]["translation"]["name"] == "Odnośnik PL"
    assert data["menuItem"]["translation"]["language"]["code"] == "PL"


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shop_create_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    site_settings,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    query = """
    mutation shopSettingsTranslate {
        shopSettingsTranslate(
                languageCode: PL, input: {headerText: "Nagłówek PL"}) {
            shop {
                translation(languageCode: PL) {
                    headerText
                    language {
                        code
                    }
                }
            }
        }
    }
    """

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["shopSettingsTranslate"]

    assert data["shop"]["translation"]["headerText"] == "Nagłówek PL"
    assert data["shop"]["translation"]["language"]["code"] == "PL"

    translation = site_settings.translations.first()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_CREATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


SHOP_SETTINGS_TRANSLATE_MUTATION = """
    mutation shopSettingsTranslate($input: ShopSettingsTranslationInput!) {
        shopSettingsTranslate(
                languageCode: PL, input: $input) {
            shop {
                translation(languageCode: PL) {
                    headerText
                    language {
                        code
                    }
                }
            }
            errors {
                field
                code
            }
        }
    }
"""


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shop_update_translation(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    site_settings,
    permission_manage_translations,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    translation = site_settings.translations.create(
        language_code="pl", header_text="Nagłówek"
    )

    response = staff_api_client.post_graphql(
        SHOP_SETTINGS_TRANSLATE_MUTATION,
        {"input": {"headerText": "Nagłówek PL"}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shopSettingsTranslate"]

    assert data["shop"]["translation"]["headerText"] == "Nagłówek PL"
    assert data["shop"]["translation"]["language"]["code"] == "PL"

    translation.refresh_from_db()
    expected_payload = generate_translation_payload(translation, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_payload,
        WebhookEventAsyncType.TRANSLATION_UPDATED,
        [any_webhook],
        translation,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_shop_translation_validates_values_lengths(
    mocked_webhook_trigger,
    staff_api_client,
    site_settings,
    permission_manage_translations,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    response = staff_api_client.post_graphql(
        SHOP_SETTINGS_TRANSLATE_MUTATION,
        {"input": {"headerText": "Nagłówek PL" * 100}},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shopSettingsTranslate"]

    assert data["shop"] is None
    assert data["errors"] == [{"field": "headerText", "code": "INVALID"}]


@pytest.mark.parametrize(
    "kind, expected_typename",
    [
        (TranslatableKinds.PRODUCT, "ProductTranslatableContent"),
        (TranslatableKinds.COLLECTION, "CollectionTranslatableContent"),
        (TranslatableKinds.CATEGORY, "CategoryTranslatableContent"),
        (TranslatableKinds.PAGE, "PageTranslatableContent"),
        (TranslatableKinds.SHIPPING_METHOD, "ShippingMethodTranslatableContent"),
        (TranslatableKinds.VOUCHER, "VoucherTranslatableContent"),
        (TranslatableKinds.SALE, "SaleTranslatableContent"),
        (TranslatableKinds.ATTRIBUTE, "AttributeTranslatableContent"),
        (TranslatableKinds.ATTRIBUTE_VALUE, "AttributeValueTranslatableContent"),
        (TranslatableKinds.VARIANT, "ProductVariantTranslatableContent"),
        (TranslatableKinds.MENU_ITEM, "MenuItemTranslatableContent"),
    ],
)
def test_translations_query(
    staff_api_client,
    permission_manage_translations,
    product,
    published_collection,
    voucher,
    sale,
    shipping_method,
    page,
    menu_item,
    kind,
    expected_typename,
):
    query = """
    query TranslationsQuery($kind: TranslatableKinds!) {
        translations(kind: $kind, first: 1) {
            edges {
                node {
                    __typename
                }
            }
            totalCount
        }
    }
    """

    response = staff_api_client.post_graphql(
        query, {"kind": kind.name}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["translations"]

    assert data["edges"][0]["node"]["__typename"] == expected_typename
    assert data["totalCount"] > 0


def test_translations_query_inline_fragment(
    staff_api_client, permission_manage_translations, product
):
    product.translations.create(language_code="pl", name="Produkt testowy")

    query = """
    {
        translations(kind: PRODUCT, first: 1) {
            edges {
                node {
                    ... on ProductTranslatableContent {
                        name
                        translation(languageCode: PL) {
                            name
                        }
                    }
                }
            }
        }
    }
    """

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["translations"]["edges"][0]

    assert data["node"]["name"] == "Test product"
    assert data["node"]["translation"]["name"] == "Produkt testowy"


QUERY_TRANSLATION_PRODUCT = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on ProductTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_product(
    staff_api_client,
    permission_manage_translations,
    product,
    product_translation_fr,
):

    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {
        "id": product_id,
        "kind": TranslatableKinds.PRODUCT.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_PRODUCT,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == product.name
    assert data["translation"]["name"] == product_translation_fr.name


QUERY_TRANSLATION_COLLECTION = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on CollectionTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_collection(
    staff_api_client,
    published_collection,
    collection_translation_fr,
    permission_manage_translations,
    channel_USD,
):

    channel_listing = published_collection.channel_listings.get()
    channel_listing.save()
    collection_id = graphene.Node.to_global_id("Collection", published_collection.id)

    variables = {
        "id": collection_id,
        "kind": TranslatableKinds.COLLECTION.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_COLLECTION,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == published_collection.name
    assert data["translation"]["name"] == collection_translation_fr.name


QUERY_TRANSLATION_CATEGORY = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on CategoryTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_category(
    staff_api_client, category, category_translation_fr, permission_manage_translations
):
    category_id = graphene.Node.to_global_id("Category", category.id)

    variables = {
        "id": category_id,
        "kind": TranslatableKinds.CATEGORY.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_CATEGORY,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == category.name
    assert data["translation"]["name"] == category_translation_fr.name


QUERY_TRANSLATION_ATTRIBUTE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on AttributeTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_attribute(
    staff_api_client, translated_attribute, permission_manage_translations
):
    attribute = translated_attribute.attribute
    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)

    variables = {
        "id": attribute_id,
        "kind": TranslatableKinds.ATTRIBUTE.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_ATTRIBUTE,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == attribute.name
    assert data["translation"]["name"] == translated_attribute.name


QUERY_TRANSLATION_ATTRIBUTE_VALUE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on AttributeValueTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_attribute_value(
    staff_api_client,
    pink_attribute_value,
    translated_attribute_value,
    permission_manage_translations,
):
    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )

    variables = {
        "id": attribute_value_id,
        "kind": TranslatableKinds.ATTRIBUTE_VALUE.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_ATTRIBUTE_VALUE,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == pink_attribute_value.name
    assert data["translation"]["name"] == translated_attribute_value.name


QUERY_TRANSLATION_VARIANT = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on ProductVariantTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_variant(
    staff_api_client,
    permission_manage_translations,
    product,
    variant,
    variant_translation_fr,
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": variant_id,
        "kind": TranslatableKinds.VARIANT.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_VARIANT,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == variant.name
    assert data["translation"]["name"] == variant_translation_fr.name


QUERY_TRANSLATION_PAGE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on PageTranslatableContent{
                id
                title
                translation(languageCode: $languageCode){
                    title
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "is_published, perm_codenames",
    [
        (True, ["manage_translations"]),
        (False, ["manage_translations"]),
        (False, ["manage_translations", "manage_pages"]),
    ],
)
def test_translation_query_page(
    staff_api_client,
    page,
    page_translation_fr,
    is_published,
    perm_codenames,
):
    page.is_published = is_published
    page.save()

    page_id = graphene.Node.to_global_id("Page", page.id)
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": page_id,
        "kind": TranslatableKinds.PAGE.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_PAGE, variables, permissions=perms
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["title"] == page.title
    assert data["translation"]["title"] == page_translation_fr.title


QUERY_TRANSLATION_SHIPPING_METHOD = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on ShippingMethodTranslatableContent{
                id
                name
                description
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "perm_codenames, return_shipping_method",
    [
        (["manage_translations"], False),
        (["manage_translations", "manage_shipping"], True),
    ],
)
def test_translation_query_shipping_method(
    staff_api_client,
    shipping_method,
    shipping_method_translation_fr,
    perm_codenames,
    return_shipping_method,
):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": shipping_method_id,
        "kind": TranslatableKinds.SHIPPING_METHOD.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_SHIPPING_METHOD, variables, permissions=perms
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["translation"]
    assert data["name"] == shipping_method.name
    assert data["description"] == shipping_method.description
    assert data["translation"]["name"] == shipping_method_translation_fr.name


QUERY_TRANSLATION_SALE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on SaleTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "perm_codenames, return_sale",
    [
        (["manage_translations"], False),
        (["manage_translations", "manage_discounts"], True),
    ],
)
def test_translation_query_sale(
    staff_api_client, sale, sale_translation_fr, perm_codenames, return_sale
):
    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": sale_id,
        "kind": TranslatableKinds.SALE.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_SALE, variables, permissions=perms
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["translation"]
    assert data["name"] == sale.name
    assert data["translation"]["name"] == sale_translation_fr.name


QUERY_TRANSLATION_VOUCHER = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on VoucherTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "perm_codenames, return_voucher",
    [
        (["manage_translations"], False),
        (["manage_translations", "manage_discounts"], True),
    ],
)
def test_translation_query_voucher(
    staff_api_client, voucher, voucher_translation_fr, perm_codenames, return_voucher
):
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": voucher_id,
        "kind": TranslatableKinds.VOUCHER.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_VOUCHER, variables, permissions=perms
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["translation"]
    assert data["name"] == voucher.name
    assert data["translation"]["name"] == voucher_translation_fr.name


QUERY_TRANSLATION_MENU_ITEM = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on MenuItemTranslatableContent{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
            }
        }
    }
"""


def test_translation_query_menu_item(
    staff_api_client,
    menu_item,
    menu_item_translation_fr,
    permission_manage_translations,
):
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)

    variables = {
        "id": menu_item_id,
        "kind": TranslatableKinds.MENU_ITEM.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_MENU_ITEM,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == menu_item.name
    assert data["translation"]["name"] == menu_item_translation_fr.name


def test_translation_query_incorrect_kind(
    staff_api_client, menu_item, permission_manage_translations
):
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)

    variables = {
        "id": menu_item_id,
        "kind": TranslatableKinds.PRODUCT.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_MENU_ITEM,
        variables,
        permissions=[permission_manage_translations],
    )
    content = get_graphql_content(response)
    assert not content["data"]["translation"]


def test_translation_query_no_permission(staff_api_client, menu_item):
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)

    variables = {
        "id": menu_item_id,
        "kind": TranslatableKinds.MENU_ITEM.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(QUERY_TRANSLATION_MENU_ITEM, variables)
    assert_no_permission(response)


def test_product_and_attribute_translation(user_api_client, product, channel_USD):
    description = dummy_editorjs("test desription")
    product.translations.create(
        language_code="pl", name="Produkt", description=description
    )
    assigned_attribute = product.attributes.first()
    attribute = assigned_attribute.attribute
    attribute.translations.create(language_code="pl", name="Kolor")

    query = """
        query productById($productId: ID!, $channel: String) {
            product(id: $productId, channel: $channel) {
                translation(languageCode: PL) {
                    name
                    description
                    descriptionJson
                    language {
                        code
                    }
                }
                attributes{
                    attribute{
                        translation(languageCode: PL){
                            id
                            name
                            language{
                                code
                            }
                        }
                    }
                }
            }
        }
    """

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = user_api_client.post_graphql(
        query, {"productId": product_id, "channel": channel_USD.slug}
    )
    data = get_graphql_content(response)["data"]

    product_translation_data = data["product"]["translation"]
    assert product_translation_data["name"] == "Produkt"
    assert product_translation_data["language"]["code"] == "PL"
    assert (
        product_translation_data["description"]
        == product_translation_data["descriptionJson"]
        == dummy_editorjs("test desription", json_format=True)
    )
    attribute_translation_data = data["product"]["attributes"][0]["attribute"][
        "translation"
    ]
    assert attribute_translation_data["name"] == "Kolor"
    assert attribute_translation_data["language"]["code"] == "PL"


PRODUCT_ATTRIBUTE_VALUES_TRANSLATION_QUERY = """
        query translation(
            $kind: TranslatableKinds!
            $id: ID!
            $languageCode: LanguageCodeEnum!
        ) {
            translation(kind: $kind, id: $id) {
                ... on ProductTranslatableContent {
                    name
                    attributeValues {
                        name
                        richText
                        plainText
                        translation(languageCode: $languageCode) {
                            name
                            richText
                            plainText
                        }
                        attribute {
                            name
                            translation(languageCode: $languageCode) {
                                name
                            }
                        }
                    }
                }
            }
        }
    """


def test_product_attribute_value_rich_text_translation(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
):
    # given
    rich_text = dummy_editorjs("Test_dummy_data")
    assigned_attribute = product_with_rich_text_attribute[0].attributes.first()
    attribute_value = assigned_attribute.attribute.values.first()
    attribute_value.translations.create(language_code="pl", rich_text=rich_text)

    product_id = graphene.Node.to_global_id(
        "Product", product_with_rich_text_attribute[0].id
    )

    query = PRODUCT_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": product_id,
        "kind": TranslatableKinds.PRODUCT.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    attribute_value_response = data["translation"]["attributeValues"][0]
    assert attribute_value_response["name"] == attribute_value.name
    assert attribute_value_response["richText"] == json.dumps(attribute_value.rich_text)
    assert attribute_value_response["translation"]["richText"] == json.dumps(rich_text)


def test_product_attribute_value_plain_text_translation(
    staff_api_client,
    plain_text_attribute,
    product,
    permission_manage_translations,
):
    # given
    product_type = product.product_type
    product_type.product_attributes.set([plain_text_attribute])

    product_attr_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        product, plain_text_attribute, product_attr_value
    )

    text = "Test plain text translation"
    product_attr_value.translations.create(language_code="pl", plain_text=text)

    product_id = graphene.Node.to_global_id("Product", product.id)

    query = PRODUCT_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": product_id,
        "kind": TranslatableKinds.PRODUCT.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    attribute_value_response = data["translation"]["attributeValues"][0]
    assert attribute_value_response["name"] == product_attr_value.name
    assert attribute_value_response["plainText"] == product_attr_value.plain_text
    assert attribute_value_response["translation"]["plainText"] == text


def test_nested_product_attribute_translation(
    staff_api_client,
    plain_text_attribute,
    product,
    permission_manage_translations,
):
    # given
    product_type = product.product_type
    product_type.product_attributes.set([plain_text_attribute])

    product_attr_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        product, plain_text_attribute, product_attr_value
    )

    text = "Test attribute translation"
    plain_text_attribute.translations.create(language_code="pl", name=text)

    product_id = graphene.Node.to_global_id("Product", product.id)

    query = PRODUCT_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": product_id,
        "kind": TranslatableKinds.PRODUCT.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    attribute_response = data["translation"]["attributeValues"][0]["attribute"]
    assert attribute_response["name"] == plain_text_attribute.name
    assert attribute_response["translation"]["name"] == text


PRODUCT_VARIANT_ATTRIBUTE_VALUES_TRANSLATION_QUERY = """
    query translation(
        $kind: TranslatableKinds!
        $id: ID!
        $languageCode: LanguageCodeEnum!
    ) {
        translation(kind: $kind, id: $id) {
            ... on ProductVariantTranslatableContent {
                name
                attributeValues {
                    name
                    richText
                    plainText
                    translation(languageCode: $languageCode) {
                        name
                        richText
                        plainText
                    }
                    attribute {
                        name
                        translation(languageCode: $languageCode) {
                            name
                        }
                    }
                }
            }
        }
    }
"""


def test_product_variant_attribute_value_rich_text_translation(
    staff_api_client,
    product_with_rich_text_attribute,
    permission_manage_translations,
    product_type_with_rich_text_attribute,
):
    # given
    rich_text = dummy_editorjs("Test_dummy_data")
    variant_attr = product_type_with_rich_text_attribute.variant_attributes.first()
    attribute_value = variant_attr.values.first()
    attribute_value.translations.create(language_code="pl", rich_text=rich_text)

    variant_id = graphene.Node.to_global_id(
        "ProductVariant", product_with_rich_text_attribute[1].id
    )

    query = PRODUCT_VARIANT_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": variant_id,
        "kind": TranslatableKinds.VARIANT.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    translations_response = data["translation"]["attributeValues"][0]
    assert translations_response["name"] == attribute_value.name
    assert translations_response["richText"] == json.dumps(attribute_value.rich_text)
    assert translations_response["translation"]["richText"] == json.dumps(rich_text)


def test_product_variant_attribute_value_plain_text_translation(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Test plain text translation"
    attribute_value.translations.create(language_code="pl", plain_text=text)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    query = PRODUCT_VARIANT_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": variant_id,
        "kind": TranslatableKinds.VARIANT.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    translations_response = data["translation"]["attributeValues"][0]
    assert translations_response["name"] == attribute_value.name
    assert translations_response["plainText"] == attribute_value.plain_text
    assert translations_response["translation"]["plainText"] == text


def test_nested_product_variant_attribute_translation(
    staff_api_client,
    variant,
    plain_text_attribute,
    permission_manage_translations,
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([plain_text_attribute])

    attribute_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant, plain_text_attribute, attribute_value
    )

    text = "Test attribute translation"
    plain_text_attribute.translations.create(language_code="pl", name=text)

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    query = PRODUCT_VARIANT_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": variant_id,
        "kind": TranslatableKinds.VARIANT.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    attribute_response = data["translation"]["attributeValues"][0]["attribute"]
    assert attribute_response["name"] == plain_text_attribute.name
    assert attribute_response["translation"]["name"] == text


PAGE_ATTRIBUTE_VALUES_TRANSLATION_QUERY = """
    query translation(
        $kind: TranslatableKinds!
        $id: ID!
        $languageCode: LanguageCodeEnum!
    ) {
        translation(kind: $kind, id: $id) {
            ... on PageTranslatableContent {
                attributeValues {
                    name
                    richText
                    plainText
                    translation(languageCode: $languageCode) {
                        name
                        richText
                        plainText
                    }
                    attribute {
                        name
                        translation(languageCode: $languageCode) {
                            name
                        }
                    }
                }
            }
        }
    }
"""


def test_page_attribute_value_rich_text_translation(
    staff_api_client,
    page_with_rich_text_attribute,
    permission_manage_translations,
    page_type_with_rich_text_attribute,
    permission_manage_pages,
):
    rich_text = dummy_editorjs("Test_dummy_data")
    variant_attr = page_type_with_rich_text_attribute.page_attributes.first()
    attribute_value = variant_attr.values.first()
    attribute_value.translations.create(language_code="pl", rich_text=rich_text)

    page_id = graphene.Node.to_global_id("Page", page_with_rich_text_attribute.id)

    query = PAGE_ATTRIBUTE_VALUES_TRANSLATION_QUERY

    variables = {
        "id": page_id,
        "kind": TranslatableKinds.PAGE.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]

    attribute_value_response = data["translation"]["attributeValues"][0]
    assert attribute_value_response["name"] == attribute_value.name
    assert attribute_value_response["richText"] == json.dumps(attribute_value.rich_text)
    assert attribute_value_response["translation"]["richText"] == json.dumps(rich_text)


def test_page_attribute_value_plain_text_translation(
    staff_api_client,
    plain_text_attribute_page_type,
    page,
    permission_manage_translations,
    permission_manage_pages,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([plain_text_attribute_page_type])
    attribute_value = plain_text_attribute_page_type.values.first()

    associate_attribute_values_to_instance(
        page, plain_text_attribute_page_type, attribute_value
    )

    text = "Test plain text translation"
    attribute_value.translations.create(language_code="pl", plain_text=text)

    page_id = graphene.Node.to_global_id("Page", page.id)

    query = PAGE_ATTRIBUTE_VALUES_TRANSLATION_QUERY

    variables = {
        "id": page_id,
        "kind": TranslatableKinds.PAGE.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    attribute_value_response = data["translation"]["attributeValues"][0]
    assert attribute_value_response["name"] == attribute_value.name
    assert attribute_value_response["plainText"] == attribute_value.plain_text
    assert attribute_value_response["translation"]["plainText"] == text


def test_nested_page_attribute_translation(
    staff_api_client,
    plain_text_attribute_page_type,
    page,
    permission_manage_translations,
    permission_manage_pages,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([plain_text_attribute_page_type])
    attribute_value = plain_text_attribute_page_type.values.first()

    associate_attribute_values_to_instance(
        page, plain_text_attribute_page_type, attribute_value
    )

    text = "Test attribute translation"
    plain_text_attribute_page_type.translations.create(language_code="pl", name=text)

    page_id = graphene.Node.to_global_id("Page", page.id)

    query = PAGE_ATTRIBUTE_VALUES_TRANSLATION_QUERY
    variables = {
        "id": page_id,
        "kind": TranslatableKinds.PAGE.name,
        "languageCode": LanguageCodeEnum.PL.name,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_translations]
    )

    # then
    data = get_graphql_content(response)["data"]

    attribute_response = data["translation"]["attributeValues"][0]["attribute"]
    assert attribute_response["name"] == plain_text_attribute_page_type.name
    assert attribute_response["translation"]["name"] == text
