import graphene
import pytest
from django.contrib.auth.models import Permission

from saleor.graphql.translations.schema import TranslatableKinds
from saleor.graphql.translations.types import LanguageCodeEnum
from tests.api.utils import get_graphql_content


def test_product_translation(user_api_client, product):
    product.translations.create(language_code="pl", name="Produkt")

    query = """
    query productById($productId: ID!) {
        product(id: $productId) {
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
    response = user_api_client.post_graphql(query, {"productId": product_id})
    data = get_graphql_content(response)["data"]

    assert data["product"]["translation"]["name"] == "Produkt"
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_variant_translation(user_api_client, variant):
    variant.translations.create(language_code="pl", name="Wariant")

    query = """
    query productVariantById($productVariantId: ID!) {
        productVariant(id: $productVariantId) {
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
        query, {"productVariantId": product_variant_id}
    )
    data = get_graphql_content(response)["data"]

    assert data["productVariant"]["translation"]["name"] == "Wariant"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"


def test_collection_translation(user_api_client, collection):
    collection.translations.create(language_code="pl", name="Kolekcja")

    query = """
    query collectionById($collectionId: ID!) {
        collection(id: $collectionId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    response = user_api_client.post_graphql(query, {"collectionId": collection_id})
    data = get_graphql_content(response)["data"]

    assert data["collection"]["translation"]["name"] == "Kolekcja"
    assert data["collection"]["translation"]["language"]["code"] == "PL"


def test_category_translation(user_api_client, category):
    category.translations.create(language_code="pl", name="Kategoria")

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

    assert data["category"]["translation"]["name"] == "Kategoria"
    assert data["category"]["translation"]["language"]["code"] == "PL"


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
    page.translations.create(language_code="pl", title="Strona")

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

    assert data["page"]["translation"]["title"] == "Strona"
    assert data["page"]["translation"]["language"]["code"] == "PL"


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
    pink_attribute_value.translations.create(language_code="pl", name="Różowy")

    query = """
    query {
        attributes(first: 1) {
            edges {
                node {
                    values {
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
    """

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = user_api_client.post_graphql(
        query, {"attributeValueId": attribute_value_id}
    )
    data = get_graphql_content(response)["data"]

    attribute_value = data["attributes"]["edges"][0]["node"]["values"][-1]
    assert attribute_value["translation"]["name"] == "Różowy"
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


def test_product_no_translation(user_api_client, product):
    query = """
    query productById($productId: ID!) {
        product(id: $productId) {
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
    response = user_api_client.post_graphql(query, {"productId": product_id})
    data = get_graphql_content(response)["data"]

    assert data["product"]["translation"] is None


def test_product_variant_no_translation(user_api_client, variant):
    query = """
    query productVariantById($productVariantId: ID!) {
        productVariant(id: $productVariantId) {
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
        query, {"productVariantId": product_variant_id}
    )
    data = get_graphql_content(response)["data"]

    assert data["productVariant"]["translation"] is None


def test_collection_no_translation(user_api_client, collection):
    query = """
    query collectionById($collectionId: ID!) {
        collection(id: $collectionId) {
            translation(languageCode: PL) {
                name
                language {
                    code
                }
            }
        }
    }
    """

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    response = user_api_client.post_graphql(query, {"collectionId": collection_id})
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
                    values {
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
    """

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = user_api_client.post_graphql(
        query, {"attributeValueId": attribute_value_id}
    )
    data = get_graphql_content(response)["data"]

    attribute_value = data["attributes"]["edges"][0]["node"]["values"][-1]
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


def test_product_create_translation(
    staff_api_client, product, permission_manage_translations
):
    query = """
    mutation productTranslate($productId: ID!) {
        productTranslate(
                id: $productId, languageCode: PL,
                input: {name: "Produkt PL"}) {
            product {
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

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = staff_api_client.post_graphql(
        query, {"productId": product_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] == "Produkt PL"
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_update_translation(
    staff_api_client, product, permission_manage_translations
):
    product.translations.create(language_code="pl", name="Produkt")

    query = """
    mutation productTranslate($productId: ID!) {
        productTranslate(
                id: $productId, languageCode: PL,
                input: {name: "Produkt PL"}) {
            product {
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

    product_id = graphene.Node.to_global_id("Product", product.id)
    response = staff_api_client.post_graphql(
        query, {"productId": product_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["productTranslate"]

    assert data["product"]["translation"]["name"] == "Produkt PL"
    assert data["product"]["translation"]["language"]["code"] == "PL"


def test_product_variant_create_translation(
    staff_api_client, variant, permission_manage_translations
):
    query = """
    mutation productVariantTranslate($productVariantId: ID!) {
        productVariantTranslate(
                id: $productVariantId, languageCode: PL,
                input: {name: "Wariant PL"}) {
            productVariant {
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

    product_variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    response = staff_api_client.post_graphql(
        query,
        {"productVariantId": product_variant_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productVariantTranslate"]

    assert data["productVariant"]["translation"]["name"] == "Wariant PL"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"


def test_product_variant_update_translation(
    staff_api_client, variant, permission_manage_translations
):
    variant.translations.create(language_code="pl", name="Wariant")

    query = """
    mutation productVariantTranslate($productVariantId: ID!) {
        productVariantTranslate(
                id: $productVariantId, languageCode: PL,
                input: {name: "Wariant PL"}) {
            productVariant {
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

    product_variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    response = staff_api_client.post_graphql(
        query,
        {"productVariantId": product_variant_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["productVariantTranslate"]

    assert data["productVariant"]["translation"]["name"] == "Wariant PL"
    assert data["productVariant"]["translation"]["language"]["code"] == "PL"


def test_collection_create_translation(
    staff_api_client, collection, permission_manage_translations
):
    query = """
    mutation collectionTranslate($collectionId: ID!) {
        collectionTranslate(
                id: $collectionId, languageCode: PL,
                input: {name: "Kolekcja PL"}) {
            collection {
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

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    response = staff_api_client.post_graphql(
        query,
        {"collectionId": collection_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"]["translation"]["name"] == "Kolekcja PL"
    assert data["collection"]["translation"]["language"]["code"] == "PL"


def test_collection_update_translation(
    staff_api_client, collection, permission_manage_translations
):
    collection.translations.create(language_code="pl", name="Kolekcja")

    query = """
    mutation collectionTranslate($collectionId: ID!) {
        collectionTranslate(
                id: $collectionId, languageCode: PL,
                input: {name: "Kolekcja PL"}) {
            collection {
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

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    response = staff_api_client.post_graphql(
        query,
        {"collectionId": collection_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["collectionTranslate"]

    assert data["collection"]["translation"]["name"] == "Kolekcja PL"
    assert data["collection"]["translation"]["language"]["code"] == "PL"


def test_category_create_translation(
    staff_api_client, category, permission_manage_translations
):
    query = """
    mutation categoryTranslate($categoryId: ID!) {
        categoryTranslate(
                id: $categoryId, languageCode: PL,
                input: {name: "Kategoria PL"}) {
            category {
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

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        query, {"categoryId": category_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]

    assert data["category"]["translation"]["name"] == "Kategoria PL"
    assert data["category"]["translation"]["language"]["code"] == "PL"


def test_category_update_translation(
    staff_api_client, category, permission_manage_translations
):
    category.translations.create(language_code="pl", name="Kategoria")

    query = """
    mutation categoryTranslate($categoryId: ID!) {
        categoryTranslate(
                id: $categoryId, languageCode: PL,
                input: {name: "Kategoria PL"}) {
            category {
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

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        query, {"categoryId": category_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["categoryTranslate"]

    assert data["category"]["translation"]["name"] == "Kategoria PL"
    assert data["category"]["translation"]["language"]["code"] == "PL"


def test_voucher_create_translation(
    staff_api_client, voucher, permission_manage_translations
):
    query = """
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

    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    response = staff_api_client.post_graphql(
        query, {"voucherId": voucher_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["voucherTranslate"]

    assert data["voucher"]["translation"]["name"] == "Bon PL"
    assert data["voucher"]["translation"]["language"]["code"] == "PL"


def test_voucher_update_translation(
    staff_api_client, voucher, permission_manage_translations
):
    voucher.translations.create(language_code="pl", name="Kategoria")

    query = """
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

    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    response = staff_api_client.post_graphql(
        query, {"voucherId": voucher_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["voucherTranslate"]

    assert data["voucher"]["translation"]["name"] == "Bon PL"
    assert data["voucher"]["translation"]["language"]["code"] == "PL"


def test_sale_create_translation(
    staff_api_client, sale, permission_manage_translations
):
    query = """
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

    sale_id = graphene.Node.to_global_id("Sale", sale.id)
    response = staff_api_client.post_graphql(
        query, {"saleId": sale_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["saleTranslate"]

    assert data["sale"]["translation"]["name"] == "Wyprz PL"
    assert data["sale"]["translation"]["language"]["code"] == "PL"


def test_page_create_translation(
    staff_api_client, page, permission_manage_translations
):
    query = """
    mutation pageTranslate($pageId: ID!) {
        pageTranslate(
                id: $pageId, languageCode: PL,
                input: {title: "Strona PL"}) {
            page {
                translation(languageCode: PL) {
                    title
                    language {
                        code
                    }
                }
            }
        }
    }
    """

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = staff_api_client.post_graphql(
        query, {"pageId": page_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]

    assert data["page"]["translation"]["title"] == "Strona PL"
    assert data["page"]["translation"]["language"]["code"] == "PL"


def test_page_update_translation(
    staff_api_client, page, permission_manage_translations
):
    page.translations.create(language_code="pl", title="Strona")

    query = """
    mutation pageTranslate($pageId: ID!) {
        pageTranslate(
                id: $pageId, languageCode: PL,
                input: {title: "Strona PL"}) {
            page {
                translation(languageCode: PL) {
                    title
                    language {
                        code
                    }
                }
            }
        }
    }
    """

    page_id = graphene.Node.to_global_id("Page", page.id)
    response = staff_api_client.post_graphql(
        query, {"pageId": page_id}, permissions=[permission_manage_translations]
    )
    data = get_graphql_content(response)["data"]["pageTranslate"]

    assert data["page"]["translation"]["title"] == "Strona PL"
    assert data["page"]["translation"]["language"]["code"] == "PL"


def test_attribute_create_translation(
    staff_api_client, color_attribute, permission_manage_translations
):
    query = """
    mutation attributeTranslate($attributeId: ID!) {
        attributeTranslate(
                id: $attributeId, languageCode: PL,
                input: {name: "Kolor PL"}) {
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

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    response = staff_api_client.post_graphql(
        query,
        {"attributeId": attribute_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeTranslate"]

    assert data["attribute"]["translation"]["name"] == "Kolor PL"
    assert data["attribute"]["translation"]["language"]["code"] == "PL"


def test_attribute_update_translation(
    staff_api_client, color_attribute, permission_manage_translations
):
    color_attribute.translations.create(language_code="pl", name="Kolor")

    query = """
    mutation attributeTranslate($attributeId: ID!) {
        attributeTranslate(
                id: $attributeId, languageCode: PL,
                input: {name: "Kolor PL"}) {
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

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    response = staff_api_client.post_graphql(
        query,
        {"attributeId": attribute_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeTranslate"]

    assert data["attribute"]["translation"]["name"] == "Kolor PL"
    assert data["attribute"]["translation"]["language"]["code"] == "PL"


def test_attribute_value_create_translation(
    staff_api_client, pink_attribute_value, permission_manage_translations
):
    query = """
    mutation attributeValueTranslate($attributeValueId: ID!) {
        attributeValueTranslate(
                id: $attributeValueId, languageCode: PL,
                input: {name: "Róż PL"}) {
            attributeValue {
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

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"attributeValueId": attribute_value_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]

    assert data["attributeValue"]["translation"]["name"] == "Róż PL"
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"


def test_attribute_value_update_translation(
    staff_api_client, pink_attribute_value, permission_manage_translations
):
    pink_attribute_value.translations.create(language_code="pl", name="Różowy")

    query = """
    mutation attributeValueTranslate($attributeValueId: ID!) {
        attributeValueTranslate(
                id: $attributeValueId, languageCode: PL,
                input: {name: "Róż PL"}) {
            attributeValue {
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

    attribute_value_id = graphene.Node.to_global_id(
        "AttributeValue", pink_attribute_value.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"attributeValueId": attribute_value_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["attributeValueTranslate"]

    assert data["attributeValue"]["translation"]["name"] == "Róż PL"
    assert data["attributeValue"]["translation"]["language"]["code"] == "PL"


def test_shipping_method_create_translation(
    staff_api_client, shipping_method, permission_manage_translations
):
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
        "ShippingMethod", shipping_method.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"shippingMethodId": shipping_method_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shippingPriceTranslate"]

    assert data["shippingMethod"]["translation"]["name"] == "DHL PL"
    assert data["shippingMethod"]["translation"]["language"]["code"] == "PL"


def test_shipping_method_update_translation(
    staff_api_client, shipping_method, permission_manage_translations
):
    shipping_method.translations.create(language_code="pl", name="DHL")

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
        "ShippingMethod", shipping_method.id
    )
    response = staff_api_client.post_graphql(
        query,
        {"shippingMethodId": shipping_method_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["shippingPriceTranslate"]

    assert data["shippingMethod"]["translation"]["name"] == "DHL PL"
    assert data["shippingMethod"]["translation"]["language"]["code"] == "PL"


def test_menu_item_update_translation(
    staff_api_client, menu_item, permission_manage_translations
):
    menu_item.translations.create(language_code="pl", name="Odnośnik")

    query = """
    mutation menuItemTranslate($menuItemId: ID!) {
        menuItemTranslate(
                id: $menuItemId, languageCode: PL,
                input: {name: "Odnośnik PL"}) {
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

    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.id)
    response = staff_api_client.post_graphql(
        query,
        {"menuItemId": menu_item_id},
        permissions=[permission_manage_translations],
    )
    data = get_graphql_content(response)["data"]["menuItemTranslate"]

    assert data["menuItem"]["translation"]["name"] == "Odnośnik PL"
    assert data["menuItem"]["translation"]["language"]["code"] == "PL"


def test_shop_create_translation(staff_api_client, permission_manage_translations):
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


def test_shop_update_translation(
    staff_api_client, site_settings, permission_manage_translations
):
    site_settings.translations.create(language_code="pl", header_text="Nagłówek")

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


@pytest.mark.parametrize(
    "kind, expected_typename",
    [
        (TranslatableKinds.PRODUCT, "Product"),
        (TranslatableKinds.COLLECTION, "Collection"),
        (TranslatableKinds.CATEGORY, "Category"),
        (TranslatableKinds.PAGE, "Page"),
        (TranslatableKinds.SHIPPING_METHOD, "ShippingMethod"),
        (TranslatableKinds.VOUCHER, "Voucher"),
        (TranslatableKinds.SALE, "Sale"),
        (TranslatableKinds.ATTRIBUTE, "Attribute"),
        (TranslatableKinds.ATTRIBUTE_VALUE, "AttributeValue"),
        (TranslatableKinds.VARIANT, "ProductVariant"),
        (TranslatableKinds.MENU_ITEM, "MenuItem"),
    ],
)
def test_translations_query(
    user_api_client,
    product,
    collection,
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
        }
    }
    """

    response = user_api_client.post_graphql(query, {"kind": kind.name})
    data = get_graphql_content(response)["data"]["translations"]

    assert data["edges"][0]["node"]["__typename"] == expected_typename


def test_translations_query_inline_fragment(user_api_client, product):
    product.translations.create(language_code="pl", name="Produkt testowy")

    query = """
    {
        translations(kind: PRODUCT, first: 1) {
            edges {
                node {
                    ... on Product {
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

    response = user_api_client.post_graphql(query)
    data = get_graphql_content(response)["data"]["translations"]["edges"][0]

    assert data["node"]["name"] == "Test product"
    assert data["node"]["translation"]["name"] == "Produkt testowy"


QUERY_TRANSLATION_PRODUCT = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on ProductStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                product{
                    id
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "is_published, perm_codenames, return_product",
    [
        (True, ["manage_translations"], True),
        (False, ["manage_translations"], False),
        (False, ["manage_translations", "manage_products"], True),
    ],
)
def test_translation_query_product(
    staff_api_client,
    product,
    product_translation_fr,
    is_published,
    perm_codenames,
    return_product,
):
    product.is_published = is_published
    product.save()

    product_id = graphene.Node.to_global_id("Product", product.id)
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": product_id,
        "kind": TranslatableKinds.PRODUCT.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_PRODUCT, variables, permissions=perms
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == product.name
    assert data["translation"]["name"] == product_translation_fr.name
    if return_product:
        assert data["product"]["name"] == product.name
    else:
        assert not data["product"]


QUERY_TRANSLATION_COLLECTION = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on CollectionStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                collection{
                    id
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "is_published, perm_codenames, return_collection",
    [
        (True, ["manage_translations"], True),
        (False, ["manage_translations"], False),
        (False, ["manage_translations", "manage_products"], True),
    ],
)
def test_translation_query_collection(
    staff_api_client,
    collection,
    collection_translation_fr,
    is_published,
    perm_codenames,
    return_collection,
):
    collection.is_published = is_published
    collection.save()

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": collection_id,
        "kind": TranslatableKinds.COLLECTION.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_COLLECTION, variables, permissions=perms
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == collection.name
    assert data["translation"]["name"] == collection_translation_fr.name
    if return_collection:
        assert data["collection"]["name"] == collection.name
    else:
        assert not data["collection"]


QUERY_TRANSLATION_CATEGORY = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on CategoryStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                category {
                    id
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
    assert data["category"]["name"] == category.name


QUERY_TRANSLATION_ATTRIBUTE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on AttributeStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                attribute {
                    id
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
    assert data["attribute"]["name"] == attribute.name


QUERY_TRANSLATION_ATTRIBUTE_VALUE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on AttributeValueStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                attributeValue {
                    id
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
    assert data["attributeValue"]["name"] == pink_attribute_value.name


QUERY_TRANSLATION_VARIANT = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on ProductVariantStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                productVariant {
                    id
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "is_published, perm_codenames, return_variant",
    [
        (True, ["manage_translations"], True),
        (False, ["manage_translations"], False),
        (False, ["manage_translations", "manage_products"], True),
    ],
)
def test_translation_query_variant(
    staff_api_client,
    product,
    variant,
    variant_translation_fr,
    is_published,
    perm_codenames,
    return_variant,
):
    product.is_published = is_published
    product.save()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    perms = list(Permission.objects.filter(codename__in=perm_codenames))

    variables = {
        "id": variant_id,
        "kind": TranslatableKinds.VARIANT.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_VARIANT, variables, permissions=perms
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["name"] == variant.name
    assert data["translation"]["name"] == variant_translation_fr.name
    if return_variant:
        assert data["productVariant"]["name"] == variant.name
    else:
        assert not data["productVariant"]


QUERY_TRANSLATION_PAGE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on PageStrings{
                id
                title
                translation(languageCode: $languageCode){
                    title
                }
                page {
                    id
                    title
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "is_published, perm_codenames, return_page",
    [
        (True, ["manage_translations"], True),
        (False, ["manage_translations"], False),
        (False, ["manage_translations", "manage_pages"], True),
    ],
)
def test_translation_query_page(
    staff_api_client,
    page,
    page_translation_fr,
    is_published,
    perm_codenames,
    return_page,
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
    if return_page:
        assert data["page"]["title"] == page.title
    else:
        assert not data["page"]


QUERY_TRANSLATION_SHIPPING_METHOD = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on ShippingMethodStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                shippingMethod {
                    id
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
        "ShippingMethod", shipping_method.id
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
    assert data["translation"]["name"] == shipping_method_translation_fr.name
    if return_shipping_method:
        assert data["shippingMethod"]["name"] == shipping_method.name
    else:
        assert not data["shippingMethod"]


QUERY_TRANSLATION_SALE = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on SaleStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                sale {
                    id
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
    if return_sale:
        assert data["sale"]["name"] == sale.name
    else:
        assert not data["sale"]


QUERY_TRANSLATION_VOUCHER = """
    query translation(
        $kind: TranslatableKinds!, $id: ID!, $languageCode: LanguageCodeEnum!
    ){
        translation(kind: $kind, id: $id){
            __typename
            ...on VoucherStrings{
                id
                name
                translation(languageCode: $languageCode){
                    name
                }
                voucher {
                    id
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
    voucher_id = graphene.Node.to_global_id("Sale", voucher.id)
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
    if return_voucher:
        assert data["voucher"]["name"] == voucher.name
    else:
        assert not data["voucher"]
