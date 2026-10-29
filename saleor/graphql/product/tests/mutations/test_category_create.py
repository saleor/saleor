import json
import os
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....core.db.locks import AdvisoryLock
from .....core.utils.json_serializer import CustomJsonEncoder
from .....product.error_codes import ProductErrorCode
from .....product.models import Category
from .....product.tests.utils import create_image
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
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


CREATE_CATEGORY_WITH_EXTERNAL_REFERENCE_MUTATION = """
    mutation createCategory($name: String!, $externalReference: String) {
        categoryCreate(
            input: {name: $name, externalReference: $externalReference}
        ) {
            category {
                name
                externalReference
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_create_category_with_external_reference(
    staff_api_client, permission_manage_products
):
    # given
    name = "test-category"
    external_reference = "test-ext-ref"
    variables = {"name": name, "externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        CREATE_CATEGORY_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryCreate"]
    assert data["errors"] == []
    assert data["category"]["externalReference"] == external_reference
    category = Category.objects.get(name=name)
    assert category.external_reference == external_reference


def test_create_category_with_non_unique_external_reference(
    staff_api_client, category, permission_manage_products
):
    # given
    external_reference = "test-ext-ref"
    category.external_reference = external_reference
    category.save(update_fields=["external_reference"])

    name = "new-category"
    variables = {"name": name, "externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        CREATE_CATEGORY_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["categoryCreate"]
    assert data["category"] is None
    assert Category.objects.filter(name=name).exists() is False
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"] == "Category with this External reference already exists."
    )
    assert errors[0]["field"] == "externalReference"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    category,
    permission_manage_products,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    category.external_reference = "existing-reference"
    category.save(update_fields=("external_reference",))
    original_name = category.name
    original_reference = category.external_reference
    name = "Changed category"
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.category_created")
    variables = {"name": name, "externalReference": "new-reference"}

    # when
    response = client.post_graphql(
        CREATE_CATEGORY_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["categoryCreate"]
        assert data["errors"] == []
        created = Category.objects.get(external_reference="new-reference")
        assert created.name == name
        assert data["category"] == {
            "name": name,
            "externalReference": created.external_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"categoryCreate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["categoryCreate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_PRODUCTS"
        )
        category.refresh_from_db(fields=("name", "external_reference"))
        assert category.name == original_name
        assert category.external_reference == original_reference
        assert Category.objects.filter(name=name).exists() is False
        webhook.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "reference_input"),
    [("omitted", {}), ("null", {"externalReference": None})],
)
def test_without_external_reference(
    _case,
    reference_input,
    staff_api_client,
    category,
    permission_manage_products,
):
    # given
    assert category.external_reference is None
    name = "Category without reference"
    variables = {"name": name, **reference_input}

    # when
    response = staff_api_client.post_graphql(
        CREATE_CATEGORY_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )

    # then
    data = get_graphql_content(response)["data"]["categoryCreate"]
    assert data["errors"] == []
    assert data["category"] == {"name": name, "externalReference": None}
    created = Category.objects.get(name=name)
    assert created.external_reference is None


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


def test_category_create_mutation_file_size_exceeds_limit(
    staff_api_client, permission_manage_products, media_root, settings
):
    # given
    settings.MAX_IMAGE_FILE_SIZE = 1
    staff_api_client.user.user_permissions.add(permission_manage_products)
    category_name = "Test category"
    image_file, image_name = create_image()
    variables = {
        "name": category_name,
        "backgroundImage": image_name,
        "backgroundImageAlt": "Alt text",
    }
    body = get_multipart_request_body(
        CATEGORY_CREATE_MUTATION, variables, image_file, image_name
    )

    # when
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["categoryCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "backgroundImage"
    assert errors[0]["code"] == ProductErrorCode.FILE_SIZE_LIMIT_EXCEEDED.name
    assert "File size exceeds the maximum allowed size" in errors[0]["message"]
    assert not Category.objects.filter(name=category_name).exists()


@pytest.mark.parametrize("_case", ["root", "child"])
def test_takes_category_tree_lock_before_insert(
    _case,
    staff_api_client,
    category,
    permission_manage_products,
    assert_advisory_lock_before_tree_write,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    category_name = "Locked category"
    category_slug = "locked-category"
    parent_pk = category.pk if _case == "child" else None
    variables = {
        "name": category_name,
        "slug": category_slug,
        "parentId": (
            graphene.Node.to_global_id("Category", parent_pk) if parent_pk else None
        ),
    }

    # when
    with assert_advisory_lock_before_tree_write(
        AdvisoryLock.CATEGORY_TREE, Category._meta.db_table
    ):
        response = staff_api_client.post_graphql(CATEGORY_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["categoryCreate"]["errors"] == []
    created_category = Category.objects.get(slug=category_slug)
    assert created_category.name == category_name
    assert created_category.parent_id == parent_pk
