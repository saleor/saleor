import json
from unittest.mock import MagicMock, Mock, patch

import graphene
import pytest
from django.core.files import File
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....product.error_codes import ProductErrorCode
from .....product.models import Category
from .....product.tests.utils import create_image, create_zip_file_with_image_ext
from .....tests.utils import dummy_editorjs
from .....thumbnail.models import Thumbnail
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    get_graphql_content,
    get_multipart_request_body,
)

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


def test_category_update_mutation_marks_prices_to_recalculate(
    staff_api_client, category, permission_manage_products, catalogue_promotion, product
):
    # given
    product.category = category
    product.save()

    staff_api_client.user.user_permissions.add(permission_manage_products)

    metadata_key = "md key"
    metadata_value = "md value"

    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "id": category_id,
        "name": "Updated name",
        "slug": "slug",
        "metadata": [{"key": metadata_key, "value": metadata_value}],
    }
    # when
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_UPDATE_MUTATION,
        variables,
    )

    # then
    get_graphql_content(response)
    assert not catalogue_promotion.rules.filter(variants_dirty=False).exists()


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
        allow_replica=False,
    )


@patch("saleor.core.tasks.delete_from_storage_task.delay")
def test_category_update_background_image_mutation(
    delete_from_storage_task_mock,
    monkeypatch,
    staff_api_client,
    category,
    permission_manage_products,
    media_root,
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
        f"https://example.com/media/category-backgrounds/{image_name}"
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
        "id": graphene.Node.to_global_id("Category", category.id),
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
        "id": graphene.Node.to_global_id("Category", category.id),
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
    ("input_slug", "expected_slug", "error_message"),
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
    ("input_slug", "expected_slug", "input_name", "error_message", "error_field"),
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
        "id": graphene.Node.to_global_id("Category", category_with_image.id),
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
