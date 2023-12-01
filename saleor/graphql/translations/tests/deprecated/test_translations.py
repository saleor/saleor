import graphene
import pytest

from ....core.enums import LanguageCodeEnum
from ....tests.utils import get_graphql_content
from ...schema import TranslatableKinds

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
                product{
                    id
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
    assert data["product"]["name"] == product.name


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
                collection{
                    id
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
    assert data["collection"]["name"] == published_collection.name


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
            ...on AttributeTranslatableContent{
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
            ...on AttributeValueTranslatableContent{
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
            ...on ProductVariantTranslatableContent{
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
    assert data["productVariant"]["name"] == variant.name


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
                page {
                    id
                    title
                }
            }
        }
    }
"""


def test_translation_query_page(
    staff_api_client,
    page,
    page_translation_fr,
    permission_manage_translations,
    permission_manage_pages,
):
    page.is_published = True
    page.save()
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {
        "id": page_id,
        "kind": TranslatableKinds.PAGE.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_PAGE,
        variables,
        permissions=[permission_manage_translations, permission_manage_pages],
    )
    content = get_graphql_content(response)
    data = content["data"]["translation"]
    assert data["title"] == page.title
    assert data["translation"]["title"] == page_translation_fr.title
    assert data["page"]["title"] == page.title


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
                shippingMethod {
                    id
                    name
                }
            }
        }
    }
"""


def test_translation_query_shipping_method(
    staff_api_client,
    shipping_method,
    shipping_method_translation_fr,
    permission_manage_translations,
    permission_manage_shipping,
):
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.id
    )
    variables = {
        "id": shipping_method_id,
        "kind": TranslatableKinds.SHIPPING_METHOD.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_SHIPPING_METHOD,
        variables,
        permissions=[permission_manage_translations, permission_manage_shipping],
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["translation"]
    assert data["name"] == shipping_method.name
    assert data["description"] == shipping_method.description
    assert data["translation"]["name"] == shipping_method_translation_fr.name
    assert data["shippingMethod"]["name"] == shipping_method.name


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
                sale {
                    id
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("perm_codenames", "return_sale"),
    [
        (["manage_translations"], False),
        (["manage_translations", "manage_discounts"], True),
    ],
)
def test_translation_query_sale(
    staff_api_client,
    promotion_converted_from_sale,
    promotion_converted_from_sale_translation_fr,
    perm_codenames,
    return_sale,
    permission_manage_translations,
    permission_manage_discounts,
):
    # given
    promotion = promotion_converted_from_sale
    promotion_translation = promotion.translations.first()
    sale_id = graphene.Node.to_global_id("Sale", promotion.old_sale_id)

    variables = {
        "id": sale_id,
        "kind": TranslatableKinds.SALE.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_SALE,
        variables,
        permissions=[permission_manage_discounts, permission_manage_translations],
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["translation"]
    assert data["name"] == promotion.name
    assert data["translation"]["name"] == promotion_translation.name
    assert data["sale"]["name"] == promotion.name


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
                voucher {
                    id
                    name
                }
            }
        }
    }
"""


def test_translation_query_voucher(
    staff_api_client,
    voucher,
    voucher_translation_fr,
    permission_manage_discounts,
    permission_manage_translations,
):
    voucher_id = graphene.Node.to_global_id("Voucher", voucher.id)
    variables = {
        "id": voucher_id,
        "kind": TranslatableKinds.VOUCHER.name,
        "languageCode": LanguageCodeEnum.FR.name,
    }
    response = staff_api_client.post_graphql(
        QUERY_TRANSLATION_VOUCHER,
        variables,
        permissions=[permission_manage_discounts, permission_manage_translations],
    )
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["translation"]
    assert data["name"] == voucher.name
    assert data["translation"]["name"] == voucher_translation_fr.name
    assert data["voucher"]["name"] == voucher.name


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
                menuItem {
                    id
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
    assert data["menuItem"]["name"] == menu_item.name
