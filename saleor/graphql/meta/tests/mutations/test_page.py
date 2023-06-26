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


def test_delete_private_metadata_for_page_attribute(
    staff_api_client, permission_manage_page_types_and_attributes, size_page_attribute
):
    # given
    size_page_attribute.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    size_page_attribute.save(update_fields=["private_metadata"])
    attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_page_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        size_page_attribute,
        attribute_id,
    )


def test_delete_private_metadata_for_page(
    staff_api_client, permission_manage_pages, page
):
    # given
    page.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page.save(update_fields=["private_metadata"])
    page_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_pages,
        page_id,
        "Page",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        page,
        page_id,
    )


def test_delete_public_metadata_for_page_attribute(
    staff_api_client, permission_manage_page_types_and_attributes, size_page_attribute
):
    # given
    size_page_attribute.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    size_page_attribute.save(update_fields=["metadata"])
    attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_page_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], size_page_attribute, attribute_id
    )


def test_delete_public_metadata_for_page(
    staff_api_client, permission_manage_pages, page
):
    # given
    page.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    page.save(update_fields=["metadata"])
    page_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_pages,
        page_id,
        "Page",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], page, page_id
    )


def test_add_public_metadata_for_page_attribute(
    staff_api_client, permission_manage_page_types_and_attributes, size_page_attribute
):
    # given
    attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_page_types_and_attributes,
        attribute_id,
        "Attribute",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], size_page_attribute, attribute_id
    )


def test_add_public_metadata_for_page(staff_api_client, permission_manage_pages, page):
    # given
    page_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_pages,
        page_id,
        "Page",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], page, page_id
    )


def test_add_private_metadata_for_page(staff_api_client, permission_manage_pages, page):
    # given
    page_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_pages,
        page_id,
        "Page",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        page,
        page_id,
    )
