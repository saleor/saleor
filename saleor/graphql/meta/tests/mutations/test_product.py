from unittest.mock import patch

import graphene

from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_private_metadata_for_product_attribute(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    # given
    color_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    color_attribute.save(update_fields=["private_metadata"])
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], color_attribute, attribute_id
    )


def test_delete_private_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    category.save(update_fields=["private_metadata"])
    category_id = graphene.Node.to_global_id("Category", category.pk)
    old_updated_at = category.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], category, category_id
    )
    category.refresh_from_db()
    assert category.updated_at > old_updated_at


def test_delete_private_metadata_for_collection(
    staff_api_client, permission_manage_products, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    collection.save(update_fields=["private_metadata"])
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], collection, collection_id
    )


def test_delete_private_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    digital_content.save(update_fields=["private_metadata"])
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        digital_content,
        digital_content_id,
    )


def test_delete_public_metadata_for_product_media(
    staff_api_client, permission_manage_products, product_with_image
):
    # given
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    media.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    media.save(update_fields=["metadata"])

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, media_id, "ProductMedia"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], media, media_id
    )


@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_delete_private_metadata_for_product(
    updated_webhook_mock, staff_api_client, permission_manage_products, product
):
    # given
    product.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product.save(update_fields=["private_metadata"])
    product_id = graphene.Node.to_global_id("Product", product.pk)
    old_updated_at = product.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], product, product_id
    )
    updated_webhook_mock.assert_called_once_with(product)
    product.refresh_from_db()
    assert product.updated_at > old_updated_at


def test_delete_private_metadata_for_product_type(
    staff_api_client, permission_manage_product_types_and_attributes, product_type
):
    # given
    product_type.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    product_type.save(update_fields=["private_metadata"])
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        product_type_id,
        "ProductType",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], product_type, product_type_id
    )


def test_delete_private_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    variant.save(update_fields=["private_metadata"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    old_updated_at = variant.updated_at

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], variant, variant_id
    )
    variant.refresh_from_db()
    assert variant.updated_at > old_updated_at


def test_delete_private_metadata_for_product_media(
    staff_api_client, permission_manage_products, product_with_image
):
    # given
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    media.store_value_in_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    media.save(update_fields=["private_metadata"])

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, media_id, "ProductMedia"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], media, media_id
    )


def test_delete_public_metadata_for_product_attribute(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    # given
    color_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    color_attribute.save(update_fields=["metadata"])
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], color_attribute, attribute_id
    )


def test_delete_public_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    category.save(update_fields=["metadata"])
    category_id = graphene.Node.to_global_id("Category", category.pk)
    old_updated_at = category.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], category, category_id
    )
    category.refresh_from_db()
    assert category.updated_at > old_updated_at


def test_delete_public_metadata_for_collection(
    staff_api_client, permission_manage_products, published_collection, channel_USD
):
    # given
    collection = published_collection
    collection.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    collection.save(update_fields=["metadata"])
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], collection, collection_id
    )


def test_delete_public_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    digital_content.save(update_fields=["metadata"])
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], digital_content, digital_content_id
    )


@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_delete_public_metadata_for_product(
    updated_webhook_mock, staff_api_client, permission_manage_products, product
):
    # given
    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    product_id = graphene.Node.to_global_id("Product", product.pk)
    old_updated_at = product.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], product, product_id
    )
    updated_webhook_mock.assert_called_once_with(product)
    product.refresh_from_db()
    assert product.updated_at > old_updated_at


def test_delete_public_metadata_for_product_type(
    staff_api_client, permission_manage_product_types_and_attributes, product_type
):
    # given
    product_type.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product_type.save(update_fields=["metadata"])
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        product_type_id,
        "ProductType",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], product_type, product_type_id
    )


def test_delete_public_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    old_updated_at = variant.updated_at

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], variant, variant_id
    )
    variant.refresh_from_db()
    assert variant.updated_at > old_updated_at


def test_add_public_metadata_for_product_media(
    staff_api_client, permission_manage_products, product_with_image
):
    # given
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, media_id, "ProductMedia"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], media, media_id
    )


def test_add_public_metadata_for_product_attribute(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    # given
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], color_attribute, attribute_id
    )


def test_add_public_metadata_for_category(
    staff_api_client, permission_manage_products, category
):
    # given
    category_id = graphene.Node.to_global_id("Category", category.pk)
    old_updated_at = category.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, category_id, "Category"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], category, category_id
    )
    category.refresh_from_db()
    assert category.updated_at > old_updated_at


def test_add_public_metadata_for_collection(
    staff_api_client, permission_manage_products, published_collection, channel_USD
):
    # given
    collection_id = graphene.Node.to_global_id("Collection", published_collection.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, collection_id, "Collection"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], published_collection, collection_id
    )


def test_add_public_metadata_for_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    # given
    digital_content_id = graphene.Node.to_global_id(
        "DigitalContent", digital_content.pk
    )

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        digital_content_id,
        "DigitalContent",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], digital_content, digital_content_id
    )


@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_add_public_metadata_for_product(
    updated_webhook_mock, staff_api_client, permission_manage_products, product
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    old_updated_at = product.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], product, product_id
    )
    updated_webhook_mock.assert_called_once_with(product)
    product.refresh_from_db()
    assert product.updated_at > old_updated_at


def test_add_public_metadata_for_product_type(
    staff_api_client, permission_manage_product_types_and_attributes, product_type
):
    # given
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        product_type_id,
        "ProductType",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], product_type, product_type_id
    )


def test_add_public_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    old_updated_at = variant.updated_at

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], variant, variant_id
    )
    variant.refresh_from_db()
    assert variant.updated_at > old_updated_at


@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_add_private_metadata_for_product(
    updated_webhook_mock, staff_api_client, permission_manage_products, product
):
    # given
    product_id = graphene.Node.to_global_id("Product", product.pk)
    old_updated_at = product.updated_at

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], product, product_id
    )
    updated_webhook_mock.assert_called_once_with(product)
    product.refresh_from_db()
    assert product.updated_at > old_updated_at


def test_add_private_metadata_for_product_type(
    staff_api_client, permission_manage_product_types_and_attributes, product_type
):
    # given
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_product_types_and_attributes,
        product_type_id,
        "ProductType",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], product_type, product_type_id
    )


def test_add_private_metadata_for_product_variant(
    staff_api_client, permission_manage_products, variant
):
    # given
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    old_updated_at = variant.updated_at

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], variant, variant_id
    )
    variant.refresh_from_db()
    assert variant.updated_at > old_updated_at


def test_add_private_metadata_for_product_media(
    staff_api_client, permission_manage_products, product_with_image
):
    # given
    media = product_with_image.media.first()
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, media_id, "ProductMedia"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], media, media_id
    )


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_update_metadata_for_product_with_use_legacy_update_webhook_emission_on(
    mocked_product_metadata_updated,
    mocked_product_updated,
    staff_api_client,
    permission_manage_products,
    product,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        product_id,
        "Product",
        value="UpdatedValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        product,
        product_id,
        value="UpdatedValue",
    )
    mocked_product_metadata_updated.assert_called_once_with(product)
    mocked_product_updated.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_update_metadata_for_product_with_use_legacy_update_webhook_emission_off(
    mocked_product_metadata_updated,
    mocked_product_updated,
    staff_api_client,
    permission_manage_products,
    product,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        product_id,
        "Product",
        value="UpdatedValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        product,
        product_id,
        value="UpdatedValue",
    )
    mocked_product_metadata_updated.assert_called_once_with(product)
    mocked_product_updated.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_update_private_metadata_for_product_use_legacy_update_webhook_emission_off(
    mocked_product_metadata_updated,
    mocked_product_updated,
    staff_api_client,
    permission_manage_products,
    product,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        product_id,
        "Product",
        value="UpdatedPrivateValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        product,
        product_id,
        value="UpdatedPrivateValue",
    )
    mocked_product_metadata_updated.assert_called_once_with(product)
    mocked_product_updated.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_update_private_metadata_for_product_use_legacy_update_webhook_emission_on(
    mocked_product_metadata_updated,
    mocked_product_updated,
    staff_api_client,
    permission_manage_products,
    product,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        product_id,
        "Product",
        value="UpdatedPrivateValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        product,
        product_id,
        value="UpdatedPrivateValue",
    )
    mocked_product_metadata_updated.assert_called_once_with(product)
    mocked_product_updated.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_delete_metadata_for_product_use_legacy_update_webhook_emission_on(
    mocked_product_metadata_updated,
    mocked_product_updated,
    staff_api_client,
    permission_manage_products,
    product,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], product, product_id
    )
    mocked_product_metadata_updated.assert_called_once_with(product)
    mocked_product_updated.assert_called_once_with(product)


@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.plugins.manager.PluginsManager.product_metadata_updated")
def test_delete_metadata_for_product_use_legacy_update_webhook_emission_off(
    mocked_product_metadata_updated,
    mocked_product_updated,
    staff_api_client,
    permission_manage_products,
    product,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    product.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    product.save(update_fields=["metadata"])
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, product_id, "Product"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], product, product_id
    )
    mocked_product_metadata_updated.assert_called_once_with(product)
    mocked_product_updated.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_metadata_for_product_variant_with_use_legacy_update_webhook_emission_on(
    mocked_variant_metadata_updated,
    mocked_variant_updated,
    staff_api_client,
    permission_manage_products,
    variant,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
        value="UpdatedValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        variant,
        variant_id,
        value="UpdatedValue",
    )
    mocked_variant_metadata_updated.assert_called_once_with(variant)
    mocked_variant_updated.assert_called_once_with(variant)


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_metadata_for_product_variant_with_use_legacy_update_webhook_emission_off(
    mocked_variant_metadata_updated,
    mocked_variant_updated,
    staff_api_client,
    permission_manage_products,
    variant,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
        value="UpdatedValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        variant,
        variant_id,
        value="UpdatedValue",
    )
    mocked_variant_metadata_updated.assert_called_once_with(variant)
    mocked_variant_updated.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_private_metadata_for_product_variant_use_legacy_update_webhook_emission_off(
    mocked_variant_metadata_updated,
    mocked_variant_updated,
    staff_api_client,
    permission_manage_products,
    variant,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
        value="UpdatedPrivateValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        variant,
        variant_id,
        value="UpdatedPrivateValue",
    )
    mocked_variant_metadata_updated.assert_called_once_with(variant)
    mocked_variant_updated.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_update_private_metadata_for_product_variant_use_legacy_update_webhook_emission_on(
    mocked_variant_metadata_updated,
    mocked_variant_updated,
    staff_api_client,
    permission_manage_products,
    variant,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_products,
        variant_id,
        "ProductVariant",
        value="UpdatedPrivateValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        variant,
        variant_id,
        value="UpdatedPrivateValue",
    )
    mocked_variant_metadata_updated.assert_called_once_with(variant)
    mocked_variant_updated.assert_called_once_with(variant)


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_delete_metadata_for_product_variant_use_legacy_update_webhook_emission_on(
    mocked_variant_metadata_updated,
    mocked_variant_updated,
    staff_api_client,
    permission_manage_products,
    variant,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = True
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], variant, variant_id
    )
    mocked_variant_metadata_updated.assert_called_once_with(variant)
    mocked_variant_updated.assert_called_once_with(variant)


@patch("saleor.plugins.manager.PluginsManager.product_variant_updated")
@patch("saleor.plugins.manager.PluginsManager.product_variant_metadata_updated")
def test_delete_metadata_for_product_variant_use_legacy_update_webhook_emission_off(
    mocked_variant_metadata_updated,
    mocked_variant_updated,
    staff_api_client,
    permission_manage_products,
    variant,
    site_settings,
):
    # given
    site_settings.use_legacy_update_webhook_emission = False
    site_settings.save(update_fields=["use_legacy_update_webhook_emission"])

    variant.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    variant.save(update_fields=["metadata"])
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, variant_id, "ProductVariant"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], variant, variant_id
    )
    mocked_variant_metadata_updated.assert_called_once_with(variant)
    mocked_variant_updated.assert_not_called()
