import graphene

from saleor.product.models import DigitalContent
from tests.api.utils import get_graphql_content
from tests.utils import create_image

from .utils import assert_read_only_mode, get_multipart_request_body


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


def test_fetch_single_digital_content(
    staff_api_client, variant, digital_content, permission_manage_products
):
    query = """
    query {
        digitalContent(id:"%s"){
            id
        }
    }
    """ % graphene.Node.to_global_id(
        "DigitalContent", digital_content.id
    )
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert "digitalContent" in content["data"]
    assert "id" in content["data"]["digitalContent"]


def test_digital_content_create_mutation_custom_settings(
    monkeypatch, staff_api_client, variant, permission_manage_products
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
    assert_read_only_mode(response)


def test_digital_content_create_mutation_default_settings(
    monkeypatch, staff_api_client, variant, permission_manage_products
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
    assert_read_only_mode(response)


def test_digital_content_create_mutation_removes_old_content(
    monkeypatch, staff_api_client, variant, permission_manage_products
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
    assert_read_only_mode(response)


def test_digital_content_delete_mutation(
    monkeypatch, staff_api_client, variant, digital_content, permission_manage_products
):
    query = """
    mutation digitalDelete($variant: ID!){
        digitalContentDelete(variantId:$variant){
            variant{
              id
            }
        }
    }
    """

    variant.digital_content = digital_content
    variant.digital_content.save()

    assert hasattr(variant, "digital_content")
    variables = {"variant": graphene.Node.to_global_id("ProductVariant", variant.id)}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)


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
    assert_read_only_mode(response)
