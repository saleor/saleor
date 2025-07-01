import json
import os
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....product.models import Category
from .....product.tests.utils import create_image
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    get_graphql_content,
    get_multipart_request_body,
)

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
        allow_replica=False,
    )


@pytest.mark.parametrize(
    ("input_slug", "expected_slug"),
    [
        ("test-slug", "test-slug"),
        (None, "test-category"),
        ("", "test-category"),
        ("わたし-わ-にっぽん-です", "わたし-わ-にっぽん-です"),
    ],
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
