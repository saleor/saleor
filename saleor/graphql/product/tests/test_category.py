import json
import os
from unittest.mock import MagicMock, Mock, patch

import graphene
import pytest
from django.core.files import File
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time
from graphql_relay import to_global_id

from ....core.utils.json_serializer import CustomJsonEncoder
from ....product.error_codes import ProductErrorCode
from ....product.models import Category, Product, ProductChannelListing
from ....product.tests.utils import create_image, create_zip_file_with_image_ext
from ....product.utils.costs import get_product_costs_data
from ....tests.utils import dummy_editorjs
from ....thumbnail.models import Thumbnail
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.payloads import generate_meta, generate_requestor
from ...core.enums import ThumbnailFormatEnum
from ...tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)

QUERY_CATEGORY = """
    query ($id: ID, $slug: String, $channel: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            ancestors(first: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            children(first: 20) {
                edges {
                    node {
                        name
                    }
                }
            }
            products(first: 10, channel: $channel) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
    """


def test_category_query_by_id(user_api_client, product, channel_USD):
    category = Category.objects.first()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert len(category_data["ancestors"]["edges"]) == category.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == category.get_children().count()


def test_category_query_invalid_id(user_api_client, product, channel_USD):
    category_id = "'"
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {category_id}."
    assert content["data"]["category"] is None


def test_category_query_object_with_given_id_does_not_exist(
    user_api_client, product, channel_USD
):
    category_id = graphene.Node.to_global_id("Category", -1)
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is None


def test_category_query_object_with_invalid_object_type(
    user_api_client, product, channel_USD
):
    category = Category.objects.first()
    category_id = graphene.Node.to_global_id("Product", category.pk)
    variables = {
        "id": category_id,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is None


def test_category_query_doesnt_show_not_available_products(
    user_api_client, product, channel_USD
):
    category = Category.objects.first()
    variant = product.variants.get()
    # Set product as not visible due to lack of price.
    variant.channel_listings.update(price_amount=None)

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert not category_data["products"]["edges"]


def test_category_query_description(user_api_client, product, channel_USD):
    category = Category.objects.first()
    description = dummy_editorjs("Test description.", json_format=True)
    category.description = dummy_editorjs("Test description.")
    category.save()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }
    query = """
    query ($id: ID, $slug: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            description
            descriptionJson
        }
    }
    """
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data["description"] == description
    assert category_data["descriptionJson"] == description


def test_category_query_without_description(user_api_client, product, channel_USD):
    category = Category.objects.first()
    category.save()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }
    query = """
    query ($id: ID, $slug: String){
        category(
            id: $id,
            slug: $slug,
        ) {
            id
            name
            description
            descriptionJson
        }
    }
    """
    response = user_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data["description"] is None
    assert category_data["descriptionJson"] == "{}"


def test_category_query_by_slug(user_api_client, product, channel_USD):
    category = Category.objects.first()
    variables = {"slug": category.slug, "channel": channel_USD.slug}
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    content = get_graphql_content(response)
    category_data = content["data"]["category"]
    assert category_data is not None
    assert category_data["name"] == category.name
    assert len(category_data["ancestors"]["edges"]) == category.get_ancestors().count()
    assert len(category_data["children"]["edges"]) == category.get_children().count()


def test_category_query_error_when_id_and_slug_provided(
    user_api_client, product, graphql_log_handler, channel_USD
):
    category = Category.objects.first()
    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "slug": category.slug,
        "channel": channel_USD.slug,
    }
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_category_query_error_when_no_param(
    user_api_client, product, graphql_log_handler
):
    variables = {}
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_query_category_product_only_visible_in_listings_as_customer(
    user_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count - 1


def test_query_category_product_visible_in_listings_as_staff_without_manage_products(
    staff_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        len(content["data"]["category"]["products"]["edges"]) == product_count - 1
    )  # invisible doesn't count


def test_query_category_product_only_visible_in_listings_as_staff_with_perm(
    staff_api_client, product_list, permission_manage_products
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count


def test_query_category_product_only_visible_in_listings_as_app_without_manage_products(
    app_api_client, product_list, channel_USD
):
    # given
    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {
        "id": graphene.Node.to_global_id("Category", category.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        len(content["data"]["category"]["products"]["edges"]) == product_count - 1
    )  # invisible doesn't count


def test_query_category_product_only_visible_in_listings_as_app_with_perm(
    app_api_client, product_list, permission_manage_products
):
    # given
    app_api_client.app.permissions.add(permission_manage_products)

    category = Category.objects.first()

    product_list[0].channel_listings.all().update(visible_in_listings=False)

    product_count = Product.objects.count()

    variables = {"id": graphene.Node.to_global_id("Category", category.pk)}

    # when
    response = app_api_client.post_graphql(QUERY_CATEGORY, variables=variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["data"]["category"]["products"]["edges"]) == product_count


CATEGORY_CREATE_MUTATION = """
        mutation(
                $name: String, $slug: String,
                $description: JSONString, $backgroundImage: Upload,
                $backgroundImageAlt: String, $parentId: ID,
                $metadata: [MetadataInput!], $privateMetadata: [MetadataInput!]) {
            categoryCreate(
                input: {
                    name: $name
                    slug: $slug
                    description: $description
                    backgroundImage: $backgroundImage
                    backgroundImageAlt: $backgroundImageAlt
                    metadata: $metadata
                    privateMetadata: $privateMetadata
                },
                parent: $parentId
            ) {
                category {
                    id
                    name
                    slug
                    description
                    parent {
                        name
                        id
                    }
                    backgroundImage{
                        alt
                    }
                    metadata {
                        key
                        value
                    }
                    privateMetadata {
                        key
                        value
                    }
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """


def test_category_create_mutation(
    monkeypatch, staff_api_client, permission_manage_products, media_root
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    category_name = "Test category"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    metadata_key = "md key"
    metadata_value = "md value"

    # test creating root category
    variables = {
        "name": category_name,
        "description": category_description,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "slug": category_slug,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
        "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
    }
    body = get_multipart_request_body(
        CATEGORY_CREATE_MUTATION, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]

    # then
    assert data["errors"] == []
    assert data["category"]["name"] == category_name
    assert data["category"]["description"] == category_description
    assert not data["category"]["parent"]
    category = Category.objects.get(name=category_name)
    assert category.description_plaintext == description
    assert category.background_image.file
    img_name, format = os.path.splitext(image_file._name)
    file_name = category.background_image.name
    assert file_name != image_file._name
    assert file_name.startswith(f"category-backgrounds/{img_name}")
    assert file_name.endswith(format)
    assert data["category"]["backgroundImage"]["alt"] == image_alt
    assert category.metadata == {metadata_key: metadata_value}
    assert category.private_metadata == {metadata_key: metadata_value}

    # test creating subcategory
    parent_id = data["category"]["id"]
    variables = {
        "name": category_name,
        "description": category_description,
        "parentId": parent_id,
        "slug": f"{category_slug}-2",
    }
    response = staff_api_client.post_graphql(CATEGORY_CREATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert data["errors"] == []
    assert data["category"]["parent"]["id"] == parent_id


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_category_create_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    monkeypatch,
    staff_api_client,
    permission_manage_products,
    media_root,
    settings,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    query = CATEGORY_CREATE_MUTATION
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    category_name = "Test category"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)
    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    # test creating root category
    variables = {
        "name": category_name,
        "description": category_description,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "slug": category_slug,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    category = Category.objects.first()

    assert category
    assert data["errors"] == []

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Category", category.id),
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.CATEGORY_CREATED,
        [any_webhook],
        category,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-category"),
        ("", "test-category"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ),
)
def test_create_category_with_given_slug(
    staff_api_client, permission_manage_products, input_slug, expected_slug
):
    query = CATEGORY_CREATE_MUTATION
    name = "Test category"
    variables = {"name": name, "slug": input_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert not data["errors"]
    assert data["category"]["slug"] == expected_slug


def test_create_category_name_with_unicode(
    staff_api_client, permission_manage_products
):
    query = CATEGORY_CREATE_MUTATION
    name = "わたし-わ にっぽん です"
    variables = {"name": name}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert not data["errors"]
    assert data["category"]["name"] == name
    assert data["category"]["slug"] == "watasi-wa-nitupon-desu"


def test_category_create_mutation_without_background_image(
    monkeypatch, staff_api_client, permission_manage_products
):
    query = CATEGORY_CREATE_MUTATION
    description = dummy_editorjs("description", True)

    # test creating root category
    category_name = "Test category"
    variables = {
        "name": category_name,
        "description": description,
        "slug": slugify(category_name),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]
    assert data["errors"] == []


MUTATION_CATEGORY_UPDATE_MUTATION = """
    mutation($id: ID!, $name: String, $slug: String,
            $backgroundImage: Upload, $backgroundImageAlt: String,
            $description: JSONString,
            $metadata: [MetadataInput!], $privateMetadata: [MetadataInput!]) {

        categoryUpdate(
            id: $id
            input: {
                name: $name
                description: $description
                backgroundImage: $backgroundImage
                backgroundImageAlt: $backgroundImageAlt
                slug: $slug
                metadata: $metadata
                privateMetadata: $privateMetadata
            }
        ) {
            category {
                id
                name
                description
                updatedAt
                parent {
                    id
                }
                backgroundImage(size: 0) {
                    alt
                    url
                }
            }
            errors {
                field
                message
            }
        }
    }
    """


def test_category_update_mutation(
    monkeypatch, staff_api_client, category, permission_manage_products, media_root
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # create child category and test that the update mutation won't change
    # it's parent
    child_category = category.children.create(name="child")

    category_name = "Updated name"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)

    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    old_meta = {"old": "meta"}
    child_category.store_value_in_metadata(items=old_meta)
    child_category.store_value_in_private_metadata(items=old_meta)
    child_category.save(update_fields=["metadata", "private_metadata"])

    metadata_key = "md key"
    metadata_value = "md value"

    category_id = graphene.Node.to_global_id("Category", child_category.pk)
    variables = {
        "name": category_name,
        "description": category_description,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "id": category_id,
        "slug": category_slug,
        "metadata": [{"key": metadata_key, "value": metadata_value}],
        "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]

    # then
    assert data["errors"] == []
    assert data["category"]["id"] == category_id
    assert data["category"]["name"] == category_name
    assert data["category"]["description"] == category_description

    parent_id = graphene.Node.to_global_id("Category", category.pk)
    assert data["category"]["parent"]["id"] == parent_id
    category = Category.objects.get(name=category_name)
    assert category.description_plaintext == description
    assert category.background_image.file
    assert data["category"]["backgroundImage"]["alt"] == image_alt
    assert category.metadata == {metadata_key: metadata_value, **old_meta}
    assert category.private_metadata == {metadata_key: metadata_value, **old_meta}


@freeze_time("2023-09-01 12:00:00")
def test_category_update_mutation_with_update_at_field(
    monkeypatch, staff_api_client, category, permission_manage_products, media_root
):
    # given
    query = MUTATION_CATEGORY_UPDATE_MUTATION

    # create child category and test that the update mutation won't change
    # it's parent
    child_category = category.children.create(name="child")

    category_name = "Updated name"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)

    category_id = graphene.Node.to_global_id("Category", child_category.pk)
    variables = {
        "name": category_name,
        "description": category_description,
        "id": category_id,
        "slug": category_slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]

    # then
    assert data["category"]["id"] == category_id
    assert data["category"]["name"] == category_name
    assert data["category"]["description"] == category_description
    assert data["category"]["updatedAt"] == timezone.now().isoformat()


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_category_update_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    monkeypatch,
    staff_api_client,
    category,
    permission_manage_products,
    media_root,
    settings,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    category_name = "Updated name"
    description = "description"
    category_slug = slugify(category_name)
    category_description = dummy_editorjs(description, True)

    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    variables = {
        "name": category_name,
        "description": category_description,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "id": graphene.Node.to_global_id("Category", category.pk),
        "slug": category_slug,
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"] == []

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.CATEGORY_UPDATED,
        [any_webhook],
        category,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_category_update_background_image_mutation(
    delete_from_storage_task_mock,
    monkeypatch,
    staff_api_client,
    category,
    permission_manage_products,
    media_root,
    site_settings,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    alt_text = "Alt text for an image."
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    thumbnail = Thumbnail.objects.create(
        category=category, size=size, image=thumbnail_mock
    )
    img_path = thumbnail.image.name

    category_name = "Updated name"

    image_file, image_name = create_image()
    image_alt = "Alt text for an image."
    category_slug = slugify(category_name)

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "name": category_name,
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "id": category_id,
        "slug": category_slug,
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"] == []
    assert data["category"]["id"] == category_id

    category = Category.objects.get(name=category_name)
    assert category.background_image.file
    assert data["category"]["backgroundImage"]["alt"] == image_alt
    assert data["category"]["backgroundImage"]["url"].startswith(
        f"http://{site_settings.site.domain}/media/category-backgrounds/{image_name}"
    )

    # ensure that thumbnails for old background image has been deleted
    assert not Thumbnail.objects.filter(category_id=category.id)
    delete_from_storage_task_mock.assert_called_once_with(img_path)


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_category_update_mutation_invalid_background_image_content_type(
    delete_from_storage_task_mock,
    staff_api_client,
    category,
    permission_manage_products,
    media_root,
):
    # given
    image_file, image_name = create_zip_file_with_image_ext()
    image_alt = "Alt text for an image."
    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(category=category, size=size, image=thumbnail_mock)

    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": to_global_id("Category", category.id),
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "isPublished": True,
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"][0]["field"] == "backgroundImage"
    assert data["errors"][0]["message"] == "Invalid file type."

    # ensure that thumbnails for old background image hasn't been deleted
    assert Thumbnail.objects.filter(category_id=category.id)
    delete_from_storage_task_mock.assert_not_called()


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_category_update_mutation_invalid_background_image(
    delete_from_storage_task_mock,
    monkeypatch,
    staff_api_client,
    category,
    permission_manage_products,
    media_root,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    image_file, image_name = create_image()
    image_alt = "Alt text for an image."

    error_msg = "Test syntax error"
    image_file_mock = Mock(side_effect=SyntaxError(error_msg))
    monkeypatch.setattr(
        "saleor.graphql.core.validators.file.Image.open", image_file_mock
    )

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(category=category, size=size, image=thumbnail_mock)

    variables = {
        "name": "new-name",
        "slug": "new-slug",
        "id": to_global_id("Category", category.id),
        "backgroundImage": image_name,
        "backgroundImageAlt": image_alt,
        "isPublished": True,
    }
    body = get_multipart_request_body(
        MUTATION_CATEGORY_UPDATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"][0]["field"] == "backgroundImage"
    assert error_msg in data["errors"][0]["message"]

    # ensure that thumbnails for old background image hasn't been deleted
    assert Thumbnail.objects.filter(category_id=category.id)
    delete_from_storage_task_mock.assert_not_called()


def test_category_update_mutation_without_background_image(
    monkeypatch, staff_api_client, category, permission_manage_products
):
    query = """
        mutation($id: ID!, $name: String, $slug: String, $description: JSONString) {
            categoryUpdate(
                id: $id
                input: {
                    name: $name
                    description: $description
                    slug: $slug
                }
            ) {
                errors {
                    field
                    message
                }
            }
        }
    """
    category_name = "Updated name"
    variables = {
        "id": graphene.Node.to_global_id(
            "Category", category.children.create(name="child").pk
        ),
        "name": category_name,
        "description": dummy_editorjs("description", True),
        "slug": slugify(category_name),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    assert data["errors"] == []


UPDATE_CATEGORY_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        categoryUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            category{
                name
                slug
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_category_slug(
    staff_api_client,
    category,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_CATEGORY_SLUG_MUTATION
    old_slug = category.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["category"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_category_slug_exists(
    staff_api_client, category, permission_manage_products
):
    query = UPDATE_CATEGORY_SLUG_MUTATION
    input_slug = "test-slug"

    second_category = Category.objects.get(pk=category.pk)
    second_category.pk = None
    second_category.slug = input_slug
    second_category.save()

    assert input_slug != category.slug

    node_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_category_slug_and_name(
    staff_api_client,
    category,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            categoryUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                category{
                    name
                    slug
                }
                errors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = category.name
    old_slug = category.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    category.refresh_from_db()
    data = content["data"]["categoryUpdate"]
    errors = data["errors"]
    if not error_message:
        assert data["category"]["name"] == input_name == category.name
        assert data["category"]["slug"] == input_slug == category.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


MUTATION_CATEGORY_DELETE = """
    mutation($id: ID!) {
        categoryDelete(id: $id) {
            category {
                name
            }
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.product.tasks.update_products_discounted_prices_task.delay")
@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_category_delete_mutation(
    delete_from_storage_task_mock,
    update_products_discounted_price_task_mock,
    staff_api_client,
    category,
    product_list,
    media_root,
    permission_manage_products,
):
    # given
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(category=category, size=128, image=thumbnail_mock)
    Thumbnail.objects.create(category=category, size=200, image=thumbnail_mock)

    category.products.add(*product_list)

    category_id = category.id

    variables = {"id": graphene.Node.to_global_id("Category", category_id)}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()
    # ensure all related thumbnails has been deleted
    assert not Thumbnail.objects.filter(category_id=category_id)
    assert delete_from_storage_task_mock.call_count == 2

    update_products_discounted_price_task_mock.assert_called_once()
    args, kwargs = update_products_discounted_price_task_mock.call_args
    assert set(kwargs["product_ids"]) == {product.id for product in product_list}


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_category_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    category,
    permission_manage_products,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name

    assert not Category.objects.first()

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.CATEGORY_DELETED,
        [any_webhook],
        category,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_delete_category_with_background_image(
    staff_api_client,
    category_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting category deletes background image from storage."""
    category = category_with_image
    variables = {"id": graphene.Node.to_global_id("Category", category.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == category.name
    with pytest.raises(category._meta.model.DoesNotExist):
        category.refresh_from_db()


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_category_delete_mutation_for_categories_tree(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    parent = categories_tree_with_published_products
    parent_product = parent.products.first()
    child_product = parent.children.first().products.first()

    product_list = [child_product, parent_product]

    variables = {"id": graphene.Node.to_global_id("Category", parent.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == parent.name
    with pytest.raises(parent._meta.model.DoesNotExist):
        parent.refresh_from_db()

    mock_update_products_discounted_prices_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_discounted_prices_task.delay.call_args
    assert set(call_kwargs["product_ids"]) == set(p.pk for p in product_list)

    product_channel_listings = ProductChannelListing.objects.filter(
        product__in=product_list
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.published_at
    assert product_channel_listings.count() == 4


@patch("saleor.product.utils.update_products_discounted_prices_task")
def test_category_delete_mutation_for_children_from_categories_tree(
    mock_update_products_discounted_prices_task,
    staff_api_client,
    categories_tree_with_published_products,
    permission_manage_products,
):
    parent = categories_tree_with_published_products
    child = parent.children.first()
    parent_product = parent.products.first()
    child_product = child.products.first()

    variables = {"id": graphene.Node.to_global_id("Category", child.id)}
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_DELETE, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryDelete"]
    assert data["category"]["name"] == child.name
    with pytest.raises(child._meta.model.DoesNotExist):
        child.refresh_from_db()

    mock_update_products_discounted_prices_task.delay.assert_called_once_with(
        product_ids=[child_product.pk]
    )

    parent_product.refresh_from_db()
    assert parent_product.category
    product_channel_listings = ProductChannelListing.objects.filter(
        product=parent_product
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is True
        assert product_channel_listing.published_at

    child_product.refresh_from_db()
    assert not child_product.category
    product_channel_listings = ProductChannelListing.objects.filter(
        product=child_product
    )
    for product_channel_listing in product_channel_listings:
        assert product_channel_listing.is_published is False
        assert not product_channel_listing.published_at


LEVELED_CATEGORIES_QUERY = """
    query leveled_categories($level: Int) {
        categories(level: $level, first: 20) {
            edges {
                node {
                    name
                    parent {
                        name
                    }
                }
            }
        }
    }
    """


def test_category_level(user_api_client, category):
    query = LEVELED_CATEGORIES_QUERY
    child = Category.objects.create(name="child", slug="chi-ld", parent=category)
    variables = {"level": 0}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content["data"]["categories"]["edges"][0]["node"]
    assert category_data["name"] == category.name
    assert category_data["parent"] is None

    variables = {"level": 1}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    category_data = content["data"]["categories"]["edges"][0]["node"]
    assert category_data["name"] == child.name
    assert category_data["parent"]["name"] == category.name


NOT_EXISTS_IDS_CATEGORIES_QUERY = """
    query ($filter: CategoryFilterInput!) {
        categories(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_categories_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_CATEGORIES_QUERY
    variables = {"filter": {"ids": ["W3KATGDn3fq3ZH4=", "zH9pYmz7yWD3Hy8="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["categories"] is None


FETCH_CATEGORY_QUERY = """
    query fetchCategory($id: ID!, $size: Int, $format: ThumbnailFormatEnum){
        category(id: $id) {
            name
            backgroundImage(size: $size, format: $format) {
                url
                alt
            }
        }
    }
    """


def test_category_image_query_with_size_and_format_proxy_url_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": 120,
        "format": format,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    assert (
        data["backgroundImage"]["url"]
        == f"http://{domain}/thumbnail/{category_id}/128/{format.lower()}/"
    )


def test_category_image_query_with_size_proxy_url_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": size,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{category_id}/{size}/"
    )


def test_category_image_query_with_size_thumbnail_url_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    size = 128
    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(category=category, size=size, image=thumbnail_mock)

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": 120,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    assert (
        data["backgroundImage"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_category_image_query_zero_size_custom_format_provided_original_image_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    format = ThumbnailFormatEnum.WEBP.name

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "format": format,
        "size": 0,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    expected_url = f"http://{domain}/media/category-backgrounds/{background_mock.name}"
    assert data["backgroundImage"]["url"] == expected_url


def test_category_image_query_zero_size_value_original_image_returned(
    user_api_client, non_default_category, media_root, site_settings
):
    # given
    alt_text = "Alt text for an image."
    category = non_default_category
    background_mock = MagicMock(spec=File)
    background_mock.name = "image.jpg"
    category.background_image = background_mock
    category.background_image_alt = alt_text
    category.save(update_fields=["background_image", "background_image_alt"])

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "size": 0,
    }

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)

    # then
    content = get_graphql_content(response)

    data = content["data"]["category"]
    assert data["backgroundImage"]["alt"] == alt_text
    domain = site_settings.site.domain
    expected_url = f"http://{domain}/media/category-backgrounds/{background_mock.name}"
    assert data["backgroundImage"]["url"] == expected_url


def test_category_image_query_without_associated_file(
    user_api_client, non_default_category
):
    # given
    category = non_default_category
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {"id": category_id}

    # when
    response = user_api_client.post_graphql(FETCH_CATEGORY_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["category"]
    assert data["name"] == category.name
    assert data["backgroundImage"] is None


def test_update_category_mutation_remove_background_image(
    staff_api_client, category_with_image, permission_manage_products
):
    query = """
        mutation updateCategory($id: ID!, $backgroundImage: Upload) {
            categoryUpdate(
                id: $id, input: {
                    backgroundImage: $backgroundImage
                }
            ) {
                category {
                    backgroundImage{
                        url
                    }
                }
                errors {
                    field
                    message
                }
            }
        }
    """
    assert category_with_image.background_image
    variables = {
        "id": to_global_id("Category", category_with_image.id),
        "backgroundImage": None,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryUpdate"]["category"]
    assert not data["backgroundImage"]
    category_with_image.refresh_from_db()
    assert not category_with_image.background_image


def test_query_category_for_federation(api_client, non_default_category):
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    variables = {
        "representations": [
            {
                "__typename": "Category",
                "id": category_id,
            },
        ],
    }
    query = """
      query GetCategoryInFederation($representations: [_Any]) {
        _entities(representations: $representations) {
          __typename
          ... on Category {
            id
            name
          }
        }
      }
    """

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Category",
            "id": category_id,
            "name": non_default_category.name,
        }
    ]


def test_query_products_no_channel_shipping_zones(
    staff_api_client, product, permission_manage_products, stock, channel_USD
):
    channel_USD.shipping_zones.clear()
    category = Category.objects.first()
    product = category.products.first()
    query = """
    query CategoryProducts($id: ID, $channel: String, $address: AddressInput) {
        category(id: $id) {
            products(first: 20, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        isAvailable(address: $address)
                    }
                }
            }
        }
    }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Category", category.id),
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is not None
    product_edges_data = content["data"]["category"]["products"]["edges"]
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]["node"]
    assert product_data["name"] == product.name
    assert product_data["isAvailable"] is False


QUERY_CATEGORIES_WITH_SORT = """
    query ($sort_by: CategorySortingInput!) {
        categories(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "category_sort, result_order",
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Cat1", "Cat2", "SubCat", "SubSubCat"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["SubSubCat", "SubCat", "Cat2", "Cat1"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "ASC"},
            ["Cat2", "SubSubCat", "Cat1", "SubCat"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "DESC"},
            ["SubCat", "Cat1", "SubSubCat", "Cat2"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "ASC"},
            ["Cat2", "SubCat", "SubSubCat", "Cat1"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "DESC"},
            ["Cat1", "SubSubCat", "SubCat", "Cat2"],
        ),
    ],
)
def test_categories_query_with_sort(
    category_sort,
    result_order,
    staff_api_client,
    permission_manage_products,
    product_type,
):
    cat1 = Category.objects.create(
        name="Cat1",
        slug="slug_category1",
        description=dummy_editorjs("Description cat1."),
    )
    Product.objects.create(
        name="Test",
        slug="test",
        product_type=product_type,
        category=cat1,
    )
    Category.objects.create(
        name="Cat2",
        slug="slug_category2",
        description=dummy_editorjs("Description cat2."),
    )
    Category.objects.create(
        name="SubCat",
        slug="slug_subcategory1",
        parent=Category.objects.get(name="Cat1"),
        description=dummy_editorjs("Subcategory_description of cat1."),
    )
    subsubcat = Category.objects.create(
        name="SubSubCat",
        slug="slug_subcategory2",
        parent=Category.objects.get(name="SubCat"),
        description=dummy_editorjs("Subcategory_description of cat1."),
    )
    Product.objects.create(
        name="Test2",
        slug="test2",
        product_type=product_type,
        category=subsubcat,
    )
    variables = {"sort_by": category_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_CATEGORIES_WITH_SORT, variables)
    content = get_graphql_content(response)
    categories = content["data"]["categories"]["edges"]

    for order, category_name in enumerate(result_order):
        assert categories[order]["node"]["name"] == category_name


@pytest.mark.parametrize(
    "category_filter, count",
    [
        ({"search": "slug_"}, 4),
        ({"search": "Category1"}, 1),
        ({"search": "cat1"}, 3),
        ({"search": "Description cat1."}, 2),
        ({"search": "Subcategory_description"}, 1),
        ({"ids": [to_global_id("Category", 2), to_global_id("Category", 3)]}, 2),
    ],
)
def test_categories_query_with_filter(
    category_filter,
    count,
    staff_api_client,
    permission_manage_products,
):
    query = """
        query ($filter: CategoryFilterInput!, ) {
              categories(first:5, filter: $filter) {
                totalCount
                edges{
                  node{
                    id
                    name
                  }
                }
              }
            }
    """

    Category.objects.create(
        id=1,
        name="Category1",
        slug="slug_category1",
        description=dummy_editorjs("Description cat1."),
        description_plaintext="Description cat1.",
    )
    Category.objects.create(
        id=2,
        name="Category2",
        slug="slug_category2",
        description=dummy_editorjs("Description cat2."),
        description_plaintext="Description cat2.",
    )

    Category.objects.create(
        id=3,
        name="SubCategory",
        slug="slug_subcategory",
        parent=Category.objects.get(name="Category1"),
        description=dummy_editorjs("Subcategory_description of cat1."),
        description_plaintext="Subcategory_description of cat1.",
    )
    Category.objects.create(
        id=4,
        name="DoubleSubCategory",
        slug="slug_subcategory4",
        description=dummy_editorjs("Super important Description cat1."),
        description_plaintext="Super important Description cat1.",
    )
    variables = {"filter": category_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["categories"]["totalCount"] == count


def test_fetch_product_from_category_query(
    staff_api_client, product, permission_manage_products, stock, channel_USD
):
    category = Category.objects.first()
    product = category.products.first()
    query = """
    query CategoryProducts($id: ID, $channel: String, $address: AddressInput) {
        category(id: $id) {
            products(first: 20, channel: $channel) {
                edges {
                    node {
                        id
                        name
                        slug
                        thumbnail{
                            url
                            alt
                        }
                        media {
                            url
                        }
                        variants {
                            name
                            channelListings {
                                costPrice {
                                    amount
                                }
                            }
                        }
                        channelListings {
                            purchaseCost {
                                start {
                                    amount
                                }
                                stop {
                                    amount
                                }
                            }
                            margin {
                                start
                                stop
                            }
                        }
                        isAvailable(address: $address)
                        pricing(address: $address) {
                            priceRange {
                                start {
                                    gross {
                                        amount
                                        currency
                                    }
                                    net {
                                        amount
                                        currency
                                    }
                                    currency
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variables = {
        "id": graphene.Node.to_global_id("Category", category.id),
        "channel": channel_USD.slug,
        "address": {"country": "US"},
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["category"] is not None
    product_edges_data = content["data"]["category"]["products"]["edges"]
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]["node"]
    assert product_data["name"] == product.name
    assert product_data["slug"] == product.slug

    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.filter(channel_id=channel_USD.id)
    purchase_cost, margin = get_product_costs_data(
        variant_channel_listing, True, channel_USD.currency_code
    )
    cost_start = product_data["channelListings"][0]["purchaseCost"]["start"]["amount"]
    cost_stop = product_data["channelListings"][0]["purchaseCost"]["stop"]["amount"]

    assert purchase_cost.start.amount == cost_start
    assert purchase_cost.stop.amount == cost_stop
    assert product_data["isAvailable"] is True
    assert margin[0] == product_data["channelListings"][0]["margin"]["start"]
    assert margin[1] == product_data["channelListings"][0]["margin"]["stop"]

    variant = product.variants.first()
    variant_channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    variant_channel_data = product_data["variants"][0]["channelListings"][0]
    variant_cost = variant_channel_data["costPrice"]["amount"]

    assert variant_channel_listing.cost_price.amount == variant_cost
