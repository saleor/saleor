from unittest.mock import patch

import graphene

from ....product.error_codes import ProductErrorCode
from ....product.models import DigitalContent, ProductVariant
from ....product.tests.utils import create_image
from ...tests.utils import (
    get_graphql_content,
    get_graphql_content_from_response,
    get_multipart_request_body,
)


def test_fetch_all_digital_contents(
    staff_api_client, variant, digital_content, permission_manage_products
):

    digital_content_num = DigitalContent.objects.count()
    query = """
    query {
        digitalContents(first:1){
            edges{
                node{
                    id
                    contentFile
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    edges = content["data"]["digitalContents"]["edges"]
    assert len(edges) == digital_content_num


QUERY_DIGITAL_CONTENT = """
    query DigitalContent($id: ID!){
        digitalContent(id: $id){
            id
            productVariant {
                id
            }
        }
    }
"""


def test_fetch_single_digital_content(
    staff_api_client, digital_content, permission_manage_products
):
    query = QUERY_DIGITAL_CONTENT
    variables = {"id": graphene.Node.to_global_id("DigitalContent", digital_content.id)}
    variant_id = graphene.Node.to_global_id(
        "ProductVariant", digital_content.product_variant.id
    )
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert "digitalContent" in content["data"]
    assert "id" in content["data"]["digitalContent"]
    assert content["data"]["digitalContent"]["productVariant"]["id"] == variant_id


def test_digital_content_query_invalid_id(
    staff_api_client, product, channel_USD, permission_manage_products
):
    digital_content_id = "'"
    variables = {
        "id": digital_content_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"] == f"Couldn't resolve id: {digital_content_id}."
    )
    assert content["data"]["digitalContent"] is None


def test_digital_content_query_object_with_given_id_does_not_exist(
    staff_api_client, product, channel_USD, permission_manage_products
):
    digital_content_id = graphene.Node.to_global_id("DigitalContent", -1)
    variables = {
        "id": digital_content_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["digitalContent"] is None


def test_digital_content_query_with_invalid_object_type(
    staff_api_client, product, digital_content, channel_USD, permission_manage_products
):
    digital_content_id = graphene.Node.to_global_id("Product", digital_content.pk)
    variables = {
        "id": digital_content_id,
        "channel": channel_USD.slug,
    }
    response = staff_api_client.post_graphql(
        QUERY_DIGITAL_CONTENT, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["digitalContent"] is None


def test_digital_content_create_mutation_custom_settings(
    monkeypatch, staff_api_client, variant, permission_manage_products, media_root
):
    query = """
    mutation createDigitalContent($variant: ID!,
        $input: DigitalContentUploadInput!) {
        digitalContentCreate(variantId: $variant, input: $input) {
            variant {
                id
            }
        }
    }
    """

    image_file, image_name = create_image()
    url_valid_days = 3
    max_downloads = 5

    variables = {
        "variant": graphene.Node.to_global_id("ProductVariant", variant.id),
        "input": {
            "useDefaultSettings": False,
            "maxDownloads": max_downloads,
            "urlValidDays": url_valid_days,
            "automaticFulfillment": True,
            "contentFile": image_name,
        },
    }

    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.digital_content.content_file
    assert variant.digital_content.max_downloads == max_downloads
    assert variant.digital_content.url_valid_days == url_valid_days
    assert variant.digital_content.automatic_fulfillment
    assert not variant.digital_content.use_default_settings


def test_digital_content_create_mutation_default_settings(
    monkeypatch, staff_api_client, variant, permission_manage_products, media_root
):
    query = """
    mutation digitalCreate($variant: ID!,
        $input: DigitalContentUploadInput!) {
        digitalContentCreate(variantId: $variant, input: $input) {
            variant {
                id
            }
        }
    }
    """

    image_file, image_name = create_image()

    variables = {
        "variant": graphene.Node.to_global_id("ProductVariant", variant.id),
        "input": {"useDefaultSettings": True, "contentFile": image_name},
    }

    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.digital_content.content_file
    assert variant.digital_content.use_default_settings


def test_digital_content_create_mutation_removes_old_content(
    monkeypatch, staff_api_client, variant, permission_manage_products, media_root
):
    query = """
    mutation digitalCreate($variant: ID!,
        $input: DigitalContentUploadInput!) {
        digitalContentCreate(variantId: $variant, input: $input) {
            variant {
                id
            }
        }
    }
    """

    image_file, image_name = create_image()

    d_content = DigitalContent.objects.create(
        content_file=image_file, product_variant=variant, use_default_settings=True
    )

    variables = {
        "variant": graphene.Node.to_global_id("ProductVariant", variant.id),
        "input": {"useDefaultSettings": True, "contentFile": image_name},
    }

    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.digital_content.content_file
    assert variant.digital_content.use_default_settings
    assert not DigitalContent.objects.filter(id=d_content.id).exists()


DIGITAL_CONTENT_DELETE_MUTATION = """
    mutation digitalDelete($variant: ID!){
        digitalContentDelete(variantId:$variant){
            variant{
              id
            }
        }
    }
"""


@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_digital_content_delete_mutation(
    delete_from_storage_task_mock,
    monkeypatch,
    staff_api_client,
    variant,
    digital_content,
    permission_manage_products,
):
    query = DIGITAL_CONTENT_DELETE_MUTATION

    variant.digital_content = digital_content
    variant.digital_content.save()

    path = digital_content.content_file.path

    assert hasattr(variant, "digital_content")
    variables = {"variant": graphene.Node.to_global_id("ProductVariant", variant.id)}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant = ProductVariant.objects.get(id=variant.id)
    assert not hasattr(variant, "digital_content")
    delete_from_storage_task_mock.assert_called_once_with(path)


def test_digital_content_update_mutation(
    monkeypatch, staff_api_client, variant, digital_content, permission_manage_products
):
    url_valid_days = 3
    max_downloads = 5
    query = """
    mutation digitalUpdate($variant: ID!, $input: DigitalContentInput!){
        digitalContentUpdate(variantId:$variant, input: $input){
            variant{
                id
            }
            content{
                contentFile
                maxDownloads
                urlValidDays
                automaticFulfillment
            }
        }
    }
    """

    digital_content.automatic_fulfillment = False
    variant.digital_content = digital_content
    variant.digital_content.save()

    variables = {
        "variant": graphene.Node.to_global_id("ProductVariant", variant.id),
        "input": {
            "maxDownloads": max_downloads,
            "urlValidDays": url_valid_days,
            "automaticFulfillment": True,
            "useDefaultSettings": False,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant = ProductVariant.objects.get(id=variant.id)
    digital_content = variant.digital_content
    assert digital_content.max_downloads == max_downloads
    assert digital_content.url_valid_days == url_valid_days
    assert digital_content.automatic_fulfillment


def test_digital_content_update_mutation_missing_content(
    monkeypatch, staff_api_client, variant, permission_manage_products
):
    url_valid_days = 3
    max_downloads = 5
    query = """
    mutation digitalUpdate($variant: ID!, $input: DigitalContentInput!){
        digitalContentUpdate(variantId:$variant, input: $input){
            variant{
                id
            }
            content{
                contentFile
                maxDownloads
                urlValidDays
                automaticFulfillment
            }
            errors {
                field
                message
            }
            errors {
                field
                message
                code
            }
        }
    }
    """

    variables = {
        "variant": graphene.Node.to_global_id("ProductVariant", variant.id),
        "input": {
            "maxDownloads": max_downloads,
            "urlValidDays": url_valid_days,
            "automaticFulfillment": True,
            "useDefaultSettings": False,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["digitalContentUpdate"]["errors"]
    errors = content["data"]["digitalContentUpdate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "variantId"

    product_errors = content["data"]["digitalContentUpdate"]["errors"]
    assert product_errors[0]["code"] == ProductErrorCode.VARIANT_NO_DIGITAL_CONTENT.name


def test_digital_content_url_create(
    monkeypatch, staff_api_client, variant, permission_manage_products, digital_content
):
    query = """
    mutation digitalContentUrlCreate($input: DigitalContentUrlCreateInput!) {
        digitalContentUrlCreate(input: $input) {
            digitalContentUrl {
                id
                url
            }
            errors {
                field
                message
            }
        }
    }
    """

    variables = {
        "input": {
            "content": graphene.Node.to_global_id("DigitalContent", digital_content.id)
        }
    }

    assert digital_content.urls.count() == 0
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    digital_content.refresh_from_db()
    assert digital_content.urls.count() == 1
