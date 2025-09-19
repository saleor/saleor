import datetime
from functools import partial
from unittest import mock
from unittest.mock import ANY

import graphene
import pytest
from django.conf import settings
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....attribute.models import AttributeValue
from .....attribute.tests.model_helpers import (
    get_page_attribute_values,
    get_page_attributes,
)
from .....attribute.utils import associate_attribute_values_to_instance
from .....page.error_codes import PageErrorCode
from .....page.models import Page
from .....product.search import update_products_search_vector
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

UPDATE_PAGE_MUTATION = """
mutation updatePage($id: ID!, $input: PageInput!) {
  pageUpdate(id: $id, input: $input) {
    page {
      id
      title
      slug
      isPublished
      publishedAt
      assignedAttributes(limit:10) {
        attribute {
          slug
        }
        ... on AssignedSingleChoiceAttribute {
          choice: value {
            name
            slug
          }
        }
        ... on AssignedNumericAttribute {
          value
        }
        ... on AssignedFileAttribute {
          file: value {
            contentType
            url
          }
        }
        ... on AssignedMultiPageReferenceAttribute {
          pages: value {
            slug
          }
        }
        ... on AssignedDateAttribute {
          date: value
        }
        ... on AssignedDateTimeAttribute {
          datetime: value
        }
        ... on AssignedTextAttribute {
          text: value
        }
        ... on AssignedPlainTextAttribute {
          plain_text: value
        }
        ... on AssignedMultiProductReferenceAttribute {
          products: value {
            slug
          }
        }
        ... on AssignedMultiProductVariantReferenceAttribute {
          variants: value {
            sku
          }
        }
        ... on AssignedMultiCategoryReferenceAttribute {
          categories: value {
            slug
          }
        }
        ... on AssignedMultiCollectionReferenceAttribute {
          collections: value {
            slug
          }
        }
        ... on AssignedSingleCategoryReferenceAttribute {
          category: value {
            slug
          }
        }
        ... on AssignedSingleCollectionReferenceAttribute {
          collection: value {
            slug
          }
        }
        ... on AssignedSinglePageReferenceAttribute {
          page: value {
            slug
          }
        }
        ... on AssignedSingleProductReferenceAttribute {
          product: value {
            slug
          }
        }
        ... on AssignedSingleProductVariantReferenceAttribute {
          variant: value {
            sku
          }
        }
      }
      attributes {
        attribute {
          slug
        }
        values {
          slug
          name
          reference
          file {
            url
            contentType
          }
          plainText
        }
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


def test_update_page(staff_api_client, permission_manage_pages, page):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)
    new_value = "Rainbow"

    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug
    assert page.search_index_dirty is False

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "slug": new_slug,
            "isPublished": True,
            "attributes": [{"id": tag_attr_id, "values": [new_value]}],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug

    size_attr, tag_attr = page_type.page_attributes.all()
    size_attr_value = get_page_attribute_values(page, size_attr).get()
    expected_attributes = [
        {
            "attribute": {"slug": size_attr.slug},
            "values": [
                {
                    "slug": size_attr_value.slug,
                    "file": None,
                    "name": size_attr_value.name,
                    "reference": None,
                    "plainText": None,
                }
            ],
        },
        {
            "attribute": {"slug": tag_attr.slug},
            "values": [
                {
                    "slug": slugify(new_value),
                    "file": None,
                    "name": new_value,
                    "plainText": None,
                    "reference": None,
                }
            ],
        },
    ]

    attributes = data["page"]["attributes"]
    assert len(attributes) == len(expected_attributes)
    for attr_data in attributes:
        assert attr_data in expected_attributes

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_size_assigned_attribute = {
        "attribute": {"slug": size_attr.slug},
        "choice": {
            "name": size_attr_value.name,
            "slug": size_attr_value.slug,
        },
    }
    expected_tag_assigned_attribute = {
        "attribute": {"slug": tag_attr.slug},
        "choice": {
            "name": new_value,
            "slug": slugify(new_value),
        },
    }
    assert expected_size_assigned_attribute in assigned_attributes
    assert expected_tag_assigned_attribute in assigned_attributes

    page.refresh_from_db()
    assert page.search_index_dirty is True


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
@freeze_time("2020-03-18 12:00:00")
def test_update_page_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_pages,
    page,
    settings,
):
    query = UPDATE_PAGE_MUTATION

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_get_webhooks_for_event.return_value = [any_webhook]

    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "slug": new_slug,
            "isPublished": True,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug
    page.published_at = timezone.now()
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PAGE_UPDATED,
        [any_webhook],
        page,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


def test_update_page_only_title(staff_api_client, permission_manage_pages, page):
    """Ensures that updating page field without providing attributes is allowed."""
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_title = page.title
    new_slug = "new-slug"
    assert new_slug != page.slug
    assert page.search_index_dirty is False

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {
            "slug": new_slug,
            "isPublished": True,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["title"] == page_title
    assert data["page"]["slug"] == new_slug

    size_attr, tag_attr = page_type.page_attributes.all()
    size_attr_value = get_page_attribute_values(page, size_attr).get()
    expected_attributes = [
        {
            "attribute": {"slug": size_attr.slug},
            "values": [
                {
                    "slug": size_attr_value.slug,
                    "file": None,
                    "name": size_attr_value.name,
                    "reference": None,
                    "plainText": None,
                }
            ],
        },
        {
            "attribute": {"slug": tag_attr.slug},
            "values": [],
        },
    ]

    attributes = data["page"]["attributes"]
    assert len(attributes) == len(expected_attributes)
    for attr_data in attributes:
        assert attr_data in expected_attributes

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_size_assigned_attribute = {
        "attribute": {"slug": size_attr.slug},
        "choice": {
            "name": size_attr_value.name,
            "slug": size_attr_value.slug,
        },
    }
    expected_tag_assigned_attribute = {
        "attribute": {"slug": tag_attr.slug},
        "choice": None,
    }
    assert expected_size_assigned_attribute in assigned_attributes
    assert expected_tag_assigned_attribute in assigned_attributes

    page.refresh_from_db()
    assert page.search_index_dirty is True


def test_update_page_with_file_attribute_value(
    staff_api_client, permission_manage_pages, page, page_file_attribute
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    page_file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_file_attribute.pk
    )
    assert page.search_index_dirty is False

    page_id = graphene.Node.to_global_id("Page", page.id)
    file_name = "test.txt"
    file_url = f"https://example.com{settings.MEDIA_URL}{file_name}"

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": page_file_attribute_id, "file": file_url}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": slugify(file_name),
                "name": file_name,
                "plainText": None,
                "reference": None,
                "file": {
                    "url": file_url,
                    "contentType": None,
                },
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "file": {
            "url": file_url,
            "contentType": None,
        },
    }
    assert expected_assigned_attribute in assigned_attributes

    # ensure updating only attributes mark the page search index as dirty
    page.refresh_from_db()
    assert page.search_index_dirty is True


def test_update_page_with_file_attribute_new_value_is_not_created(
    staff_api_client, permission_manage_pages, page, page_file_attribute
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    page_file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_file_attribute.pk
    )
    existing_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(
        page, {page_file_attribute.pk: [existing_value]}
    )

    page_id = graphene.Node.to_global_id("Page", page.id)
    file_url = f"https://example.com{settings.MEDIA_URL}{existing_value.file_url}"

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": page_file_attribute_id, "file": file_url}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": existing_value.slug,
                "name": existing_value.name,
                "plainText": None,
                "reference": None,
                "file": {
                    "url": file_url,
                    "contentType": existing_value.content_type,
                },
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "file": {
            "url": file_url,
            "contentType": existing_value.content_type,
        },
    }
    assert expected_assigned_attribute in assigned_attributes


def test_update_page_clear_file_attribute_values(
    staff_api_client, permission_manage_pages, page, page_file_attribute
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    page_file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_file_attribute.pk
    )
    existing_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(
        page, {page_file_attribute.pk: [existing_value]}
    )

    attribute = page_file_attribute
    attribute.value_required = False
    attribute.save(update_fields=["value_required"])

    page_file_attribute_id = graphene.Node.to_global_id("Attribute", attribute.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": page_file_attribute_id, "file": ""}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    assert not data["errors"]
    assert data["page"]
    attr_data = [
        attr
        for attr in data["page"]["attributes"]
        if attr["attribute"]["slug"] == attribute.slug
    ][0]
    assert not attr_data["values"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "file": None,
    }
    assert expected_assigned_attribute in assigned_attributes
    assert not get_page_attribute_values(page, page_file_attribute).exists()


def test_update_page_with_page_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    ref_page = page_list[1]
    page_type = page.page_type
    page_type.page_attributes.add(page_type_page_reference_attribute)

    values_count = page_type_page_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Page", ref_page.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{ref_page.pk}",
                "name": page.title,
                "file": None,
                "plainText": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "pages": [{"slug": ref_page.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count + 1


def test_update_page_with_page_reference_attribute_existing_value(
    staff_api_client,
    permission_manage_pages,
    page_list,
    page_type_page_reference_attribute,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    ref_page = page_list[1]
    page_type = page.page_type
    page_type.page_attributes.add(page_type_page_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{ref_page.pk}",
        reference_page=ref_page,
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attr_value]}
    )

    values_count = page_type_page_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Page", ref_page.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "values": [
            {
                "slug": attr_value.slug,
                "file": None,
                "name": page.title,
                "plainText": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "pages": [{"slug": ref_page.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count


def test_update_page_with_plain_text_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page_list,
    plain_text_attribute_page_type,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    page_type = page.page_type
    page_type.page_attributes.add(plain_text_attribute_page_type)

    values_count = plain_text_attribute_page_type.values.count()
    attribute_id = graphene.Node.to_global_id(
        "Attribute", plain_text_attribute_page_type.pk
    )
    text = "test plain text attribute content"

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": attribute_id, "plainText": text}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": plain_text_attribute_page_type.slug},
        "values": [
            {
                "slug": f"{page.pk}_{plain_text_attribute_page_type.pk}",
                "name": text,
                "file": None,
                "reference": None,
                "plainText": text,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": plain_text_attribute_page_type.slug},
        "plain_text": text,
    }
    assert expected_assigned_attribute in assigned_attributes

    plain_text_attribute_page_type.refresh_from_db()
    assert plain_text_attribute_page_type.values.count() == values_count + 1


def test_update_page_with_reference_attributes_and_reference_types_defined(
    staff_api_client,
    page_list,
    page,
    product,
    variant,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    page_type_variant_reference_attribute,
    permission_manage_pages,
    permission_manage_products,
):
    # given
    page.page_type.page_attributes.clear()
    page.page_type.page_attributes.add(
        page_type_page_reference_attribute,
        page_type_product_reference_attribute,
        page_type_variant_reference_attribute,
    )

    reference_page = page_list[1]

    page_type_page_reference_attribute.reference_page_types.add(
        reference_page.page_type
    )
    page_type_product_reference_attribute.reference_product_types.add(
        product.product_type
    )
    page_type_variant_reference_attribute.reference_product_types.add(
        variant.product.product_type
    )

    page_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.id
    )
    product_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.id
    )
    variant_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", page_type_variant_reference_attribute.id
    )
    page_ref = graphene.Node.to_global_id("Page", reference_page.pk)
    product_ref = graphene.Node.to_global_id("Product", product.pk)
    variant_ref = graphene.Node.to_global_id("ProductVariant", variant.pk)

    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {
        "id": page_id,
        "input": {
            "attributes": [
                {"id": page_ref_attr_id, "references": [page_ref]},
                {"id": product_ref_attr_id, "references": [product_ref]},
                {"id": variant_ref_attr_id, "references": [variant_ref]},
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_pages, permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    assert not data["errors"]
    attributes_data = data["page"]["attributes"]
    assert len(attributes_data) == len(variables["input"]["attributes"])
    expected_attributes_data = [
        {
            "attribute": {"slug": page_type_page_reference_attribute.slug},
            "values": [
                {
                    "id": ANY,
                    "slug": f"{page.pk}_{reference_page.pk}",
                    "file": None,
                    "plainText": None,
                    "reference": page_ref,
                    "name": reference_page.title,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
        {
            "attribute": {"slug": page_type_product_reference_attribute.slug},
            "values": [
                {
                    "id": ANY,
                    "slug": f"{page.pk}_{product.pk}",
                    "file": None,
                    "plainText": None,
                    "reference": product_ref,
                    "name": product.name,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
        {
            "attribute": {"slug": page_type_variant_reference_attribute.slug},
            "values": [
                {
                    "id": ANY,
                    "slug": f"{page.pk}_{variant.pk}",
                    "file": None,
                    "plainText": None,
                    "reference": variant_ref,
                    "name": f"{variant.product.name}: {variant.name}",
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
    ]
    for attr_data in attributes_data:
        assert attr_data in expected_attributes_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_page_ref_assigned_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "pages": [{"slug": reference_page.slug}],
    }
    assert expected_page_ref_assigned_attribute in assigned_attributes
    expected_product_ref_assigned_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "products": [{"slug": product.slug}],
    }
    assert expected_product_ref_assigned_attribute in assigned_attributes
    expected_variant_ref_assigned_attribute = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "variants": [{"sku": variant.sku}],
    }
    assert expected_variant_ref_assigned_attribute in assigned_attributes


def test_update_page_with_plain_text_attribute_existing_value(
    staff_api_client,
    permission_manage_pages,
    page_list,
    plain_text_attribute_page_type,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    page_type = page.page_type
    page_type.page_attributes.add(plain_text_attribute_page_type)

    values_count = plain_text_attribute_page_type.values.count()
    attribute_id = graphene.Node.to_global_id(
        "Attribute", plain_text_attribute_page_type.pk
    )
    attribute_value = plain_text_attribute_page_type.values.first()
    attribute_value.slug = f"{page.pk}_{plain_text_attribute_page_type.pk}"
    attribute_value.save(update_fields=["slug"])

    text = attribute_value.plain_text

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": attribute_id, "plainText": text}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": plain_text_attribute_page_type.slug},
        "values": [
            {
                "slug": attribute_value.slug,
                "name": text,
                "file": None,
                "reference": None,
                "plainText": text,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": plain_text_attribute_page_type.slug},
        "plain_text": text,
    }
    assert expected_assigned_attribute in assigned_attributes

    plain_text_attribute_page_type.refresh_from_db()
    assert plain_text_attribute_page_type.values.count() == values_count


@pytest.mark.parametrize("value", ["", "  ", None])
def test_update_page_with_required_plain_text_attribute_empty_value(
    value,
    staff_api_client,
    permission_manage_pages,
    page_list,
    plain_text_attribute_page_type,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page = page_list[0]
    page_type = page.page_type
    page_type.page_attributes.add(plain_text_attribute_page_type)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", plain_text_attribute_page_type.pk
    )
    attribute_value = plain_text_attribute_page_type.values.first()
    attribute_value.slug = f"{page.pk}_{plain_text_attribute_page_type.pk}"
    attribute_value.save(update_fields=["slug"])

    plain_text_attribute_page_type.value_required = True
    plain_text_attribute_page_type.save(update_fields=["value_required"])

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": attribute_id, "plainText": value}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    errors = data["errors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"


def test_update_page_with_product_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_product_reference_attribute,
    product,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    values_count = page_type_product_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Product", product.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{product.pk}",
                "name": product.name,
                "file": None,
                "plainText": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "products": [{"slug": product.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_product_reference_attribute.refresh_from_db()
    assert page_type_product_reference_attribute.values.count() == values_count + 1


def test_update_page_with_product_reference_attribute_existing_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_product_reference_attribute,
    product,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    expected_name = product.name
    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=expected_name,
        slug=f"{page.pk}_{product.pk}",
        reference_product=product,
    )
    associate_attribute_values_to_instance(
        page, {page_type_product_reference_attribute.pk: [attr_value]}
    )

    values_count = page_type_product_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Product", product.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "values": [
            {
                "slug": attr_value.slug,
                "file": None,
                "name": expected_name,
                "reference": reference,
                "plainText": None,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "products": [{"slug": product.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_product_reference_attribute.refresh_from_db()
    assert page_type_product_reference_attribute.values.count() == values_count


def test_update_page_with_variant_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_variant_reference_attribute,
    variant,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_variant_reference_attribute)

    values_count = page_type_variant_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_variant_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("ProductVariant", variant.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{variant.pk}",
                "name": f"{variant.product.name}: {variant.name}",
                "file": None,
                "plainText": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "variants": [{"sku": variant.sku}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_variant_reference_attribute.refresh_from_db()
    assert page_type_variant_reference_attribute.values.count() == values_count + 1


def test_update_page_with_variant_reference_attribute_existing_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_variant_reference_attribute,
    variant,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_variant_reference_attribute)

    expected_name = f"{variant.product.name}: {variant.name}"
    attr_value = AttributeValue.objects.create(
        attribute=page_type_variant_reference_attribute,
        name=expected_name,
        slug=f"{page.pk}_{variant.pk}",
        reference_variant=variant,
    )
    associate_attribute_values_to_instance(
        page, {page_type_variant_reference_attribute.pk: [attr_value]}
    )

    values_count = page_type_variant_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_variant_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("ProductVariant", variant.pk)

    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "values": [
            {
                "slug": attr_value.slug,
                "file": None,
                "name": expected_name,
                "reference": reference,
                "plainText": None,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "variants": [{"sku": variant.sku}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_variant_reference_attribute.refresh_from_db()
    assert page_type_variant_reference_attribute.values.count() == values_count


def test_update_page_with_category_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_category_reference_attribute,
    category,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_category_reference_attribute)
    values_count = page_type_category_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_category_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Category", category.pk)
    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_category_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{category.pk}",
                "name": category.name,
                "file": None,
                "plainText": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_category_reference_attribute.slug},
        "categories": [{"slug": category.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_category_reference_attribute.refresh_from_db()
    assert page_type_category_reference_attribute.values.count() == values_count + 1


def test_update_page_with_collection_reference_attribute_new_value(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_collection_reference_attribute,
    collection,
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_collection_reference_attribute)
    values_count = page_type_collection_reference_attribute.values.count()
    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_collection_reference_attribute.pk
    )
    reference = graphene.Node.to_global_id("Collection", collection.pk)
    page_id = graphene.Node.to_global_id("Page", page.id)

    variables = {
        "id": page_id,
        "input": {"attributes": [{"id": ref_attribute_id, "references": [reference]}]},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]
    updated_attribute = {
        "attribute": {"slug": page_type_collection_reference_attribute.slug},
        "values": [
            {
                "slug": f"{page.pk}_{collection.pk}",
                "name": collection.name,
                "file": None,
                "plainText": None,
                "reference": reference,
            }
        ],
    }
    assert updated_attribute in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_collection_reference_attribute.slug},
        "collections": [{"slug": collection.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_collection_reference_attribute.refresh_from_db()
    assert page_type_collection_reference_attribute.values.count() == values_count + 1


def test_update_page_with_reference_attributes_ref_not_in_available_choices(
    staff_api_client,
    page_list,
    product,
    variant,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    page_type_variant_reference_attribute,
    permission_manage_pages,
    product_type_with_variant_attributes,
    page_type_with_rich_text_attribute,
):
    # given
    page = page_list[0]
    page.page_type.page_attributes.clear()
    page.page_type.page_attributes.add(
        page_type_page_reference_attribute,
        page_type_product_reference_attribute,
        page_type_variant_reference_attribute,
    )

    reference_page = page_list[1]
    # assigned reference types that do not match product/page types of references
    # that are provided in the input
    page_type_page_reference_attribute.reference_page_types.add(
        page_type_with_rich_text_attribute
    )
    page_type_product_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )
    page_type_variant_reference_attribute.reference_product_types.add(
        product_type_with_variant_attributes
    )

    page_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.id
    )
    product_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.id
    )
    variant_ref_attr_id = graphene.Node.to_global_id(
        "Attribute", page_type_variant_reference_attribute.id
    )
    variant_ref = graphene.Node.to_global_id("ProductVariant", variant.pk)
    page_ref = graphene.Node.to_global_id("Page", reference_page.pk)
    product_ref = graphene.Node.to_global_id("Product", product.pk)

    page_id = graphene.Node.to_global_id("Page", page.pk)
    variables = {
        "id": page_id,
        "input": {
            "attributes": [
                {"id": page_ref_attr_id, "references": [page_ref]},
                {"id": product_ref_attr_id, "references": [product_ref]},
                {"id": variant_ref_attr_id, "references": [variant_ref]},
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_pages],
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["pageUpdate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.INVALID.name
    assert errors[0]["field"] == "attributes"
    assert set(errors[0]["attributes"]) == {
        page_ref_attr_id,
        product_ref_attr_id,
        variant_ref_attr_id,
    }


@freeze_time("2020-03-18 12:00:00")
def test_public_page_sets_publication_date(
    staff_api_client, permission_manage_pages, page_type
):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": dummy_editorjs("Content for page 1"),
        "is_published": False,
        "page_type": page_type,
    }
    page = Page.objects.create(**data)
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "input": {"isPublished": True, "slug": page.slug}}
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["isPublished"] is True
    assert (
        data["page"]["publishedAt"]
        == datetime.datetime.now(tz=datetime.UTC).isoformat()
    )


def test_update_page_publication_date(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    data = {
        "slug": "test-url",
        "title": "Test page",
        "page_type": page_type,
        "search_index_dirty": False,
    }
    page = Page.objects.create(**data)
    published_at = datetime.datetime.now(tz=datetime.UTC).replace(
        microsecond=0
    ) + datetime.timedelta(days=5)
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {
        "id": page_id,
        "input": {"isPublished": True, "publishedAt": published_at},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["isPublished"] is True
    assert data["page"]["publishedAt"] == published_at.isoformat()

    # ensure that updating publish dates do not affect search_index_dirty flag
    page.refresh_from_db()
    assert page.search_index_dirty is False


@pytest.mark.parametrize("slug_value", [None, ""])
def test_update_page_blank_slug_value(
    staff_api_client, permission_manage_pages, page, slug_value
):
    query = UPDATE_PAGE_MUTATION
    assert slug_value != page.slug

    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "input": {"slug": slug_value, "isPublished": True}}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageUpdate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


@pytest.mark.parametrize("slug_value", [None, ""])
def test_update_page_with_title_value_and_without_slug_value(
    staff_api_client, permission_manage_pages, page, slug_value
):
    query = """
        mutation updatePage($id: ID!, $title: String, $slug: String) {
        pageUpdate(id: $id, input: {title: $title, slug: $slug}) {
            page {
                id
                title
                slug
            }
            errors {
                field
                code
                message
            }
        }
    }
    """
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {"id": page_id, "title": "test", "slug": slug_value}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageUpdate"]["errors"]

    assert len(errors) == 1
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name


UPDATE_PAGE_ATTRIBUTES_MUTATION = """
    mutation updatePage(
        $id: ID!, $input: PageInput!
    ) {
        pageUpdate(
            id: $id, input: $input
        ) {
            page {
                id
                title
                slug
                assignedAttributes(limit:10) {
                    attribute {
                        slug
                    }
                    ... on AssignedMultiProductReferenceAttribute {
                        products: value {
                            slug
                        }
                    }
                    ... on AssignedMultiProductVariantReferenceAttribute {
                        variants: value {
                            sku
                        }
                    }
                    ... on AssignedMultiCategoryReferenceAttribute {
                        categories: value {
                            slug
                        }
                    }
                    ... on AssignedMultiCollectionReferenceAttribute {
                        collections: value {
                            slug
                        }
                    }
                    ... on AssignedMultiPageReferenceAttribute {
                        pages: value {
                            slug
                        }
                    }
                    ... on AssignedSingleCategoryReferenceAttribute {
                        category: value {
                            slug
                        }
                    }
                    ... on AssignedSingleCollectionReferenceAttribute {
                        collection: value {
                            slug
                        }
                    }
                    ... on AssignedSinglePageReferenceAttribute {
                        page: value {
                            slug
                        }
                    }
                    ... on AssignedSingleProductReferenceAttribute {
                        product: value {
                            slug
                        }
                    }
                    ... on AssignedSingleProductVariantReferenceAttribute {
                        variant: value {
                            sku
                        }
                    }
                }
                attributes {
                    attribute {
                        slug
                    }
                    values {
                        id
                        slug
                        name
                        reference
                        date
                        dateTime
                        plainText
                        file {
                            url
                            contentType
                        }
                    }
                }
            }
            errors {
                field
                code
                message
                attributes
            }
        }
    }
"""


def test_update_page_change_attribute_values_ordering(
    staff_api_client,
    permission_manage_pages,
    page,
    product_list,
    page_type_product_reference_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.set([page_type_product_reference_attribute])

    page_id = graphene.Node.to_global_id("Page", page.pk)

    attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )

    attr_value_1 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{page.pk}_{product_list[0].pk}",
        reference_product=product_list[0],
    )
    attr_value_2 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[1].name,
        slug=f"{page.pk}_{product_list[1].pk}",
        reference_product=product_list[1],
    )
    attr_value_3 = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=product_list[2].name,
        slug=f"{page.pk}_{product_list[2].pk}",
        reference_product=product_list[2],
    )

    associate_attribute_values_to_instance(
        page,
        {
            page_type_product_reference_attribute.pk: [
                attr_value_3,
                attr_value_2,
                attr_value_1,
            ]
        },
    )

    attribute = get_page_attributes(page).first()
    assert attribute is not None
    assert list(
        get_page_attribute_values(page, attribute).values_list("id", flat=True)
    ) == [attr_value_3.pk, attr_value_2.pk, attr_value_1.pk]

    expected_first_product = product_list[1]
    expected_second_product = product_list[0]
    expected_third_product = product_list[2]

    new_ref_order = [
        expected_first_product,
        expected_second_product,
        expected_third_product,
    ]
    variables = {
        "id": page_id,
        "input": {
            "attributes": [
                {
                    "id": attribute_id,
                    "references": [
                        graphene.Node.to_global_id("Product", ref.pk)
                        for ref in new_ref_order
                    ],
                }
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_pages],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    assert data["errors"] == []

    attributes = data["page"]["attributes"]

    assert len(attributes) == 1
    values = attributes[0]["values"]
    assert len(values) == 3
    assert [value["id"] for value in values] == [
        graphene.Node.to_global_id("AttributeValue", val.pk)
        for val in [attr_value_2, attr_value_1, attr_value_3]
    ]

    assigned_attributes = data["page"]["assignedAttributes"]
    assert len(assigned_attributes) == 1
    assigned_values = assigned_attributes[0]["products"]
    assert len(assigned_values) == 3
    assert assigned_values[0]["slug"] == expected_first_product.slug
    assert assigned_values[1]["slug"] == expected_second_product.slug
    assert assigned_values[2]["slug"] == expected_third_product.slug

    assert list(
        get_page_attribute_values(page, attribute).values_list("id", flat=True)
    ) == [attr_value_2.pk, attr_value_1.pk, attr_value_3.pk]


def test_paginate_pages(user_api_client, page, page_type):
    page.is_published = True
    data_02 = {
        "slug": "test02-url",
        "title": "Test page",
        "content": dummy_editorjs("Content for page 1"),
        "is_published": True,
        "page_type": page_type,
    }
    data_03 = {
        "slug": "test03-url",
        "title": "Test page",
        "content": dummy_editorjs("Content for page 1"),
        "is_published": True,
        "page_type": page_type,
    }

    Page.objects.create(**data_02)
    Page.objects.create(**data_03)
    query = """
        query PagesQuery {
            pages(first: 2) {
                edges {
                    node {
                        id
                        title
                    }
                }
            }
        }
        """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    pages_data = content["data"]["pages"]
    assert len(pages_data["edges"]) == 2


def test_update_page_with_single_reference_attributes(
    staff_api_client,
    permission_manage_pages,
    page_list,
    page_type_page_single_reference_attribute,
    page_type_product_single_reference_attribute,
    page_type_variant_single_reference_attribute,
    page_type_category_single_reference_attribute,
    page_type_collection_single_reference_attribute,
    collection,
    product,
    categories,
    product_variant_list,
):
    # given
    page = page_list[0]
    page.page_type.page_attributes.clear()
    page.page_type.page_attributes.add(
        page_type_page_single_reference_attribute,
        page_type_product_single_reference_attribute,
        page_type_variant_single_reference_attribute,
        page_type_category_single_reference_attribute,
        page_type_collection_single_reference_attribute,
    )
    page_ref = page_list[1]
    references = [
        (page_ref, page_type_page_single_reference_attribute, page_ref.title),
        (product, page_type_product_single_reference_attribute, product.name),
        (
            product_variant_list[0],
            page_type_variant_single_reference_attribute,
            f"{product_variant_list[0].product.name}: {product_variant_list[0].name}",
        ),
        (
            categories[0],
            page_type_category_single_reference_attribute,
            categories[0].name,
        ),
        (
            collection,
            page_type_collection_single_reference_attribute,
            collection.name,
        ),
    ]
    attributes = [
        {
            "id": graphene.Node.to_global_id("Attribute", attr.pk),
            "reference": graphene.Node.to_global_id(attr.entity_type, ref.pk),
        }
        for ref, attr, _name in references
    ]

    variables = {
        "id": graphene.Node.to_global_id("Page", page.pk),
        "input": {
            "attributes": attributes,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_pages],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    errors = data["errors"]

    assert not errors
    attributes_data = data["page"]["attributes"]
    assert len(attributes_data) == len(references)
    expected_attributes_data = [
        {
            "attribute": {
                "slug": attr.slug,
            },
            "values": [
                {
                    "id": ANY,
                    "slug": f"{page.id}_{ref.id}",
                    "date": None,
                    "dateTime": None,
                    "name": name,
                    "file": None,
                    "plainText": None,
                    "reference": graphene.Node.to_global_id(attr.entity_type, ref.pk),
                }
            ],
        }
        for ref, attr, name in references
    ]
    for attr_data in attributes_data:
        assert attr_data in expected_attributes_data

    assigned_attributes = data["page"]["assignedAttributes"]

    expected_assigned_page_attribute = {
        "attribute": {"slug": page_type_page_single_reference_attribute.slug},
        "page": {"slug": page_ref.slug},
    }
    expected_assigned_product_attribute = {
        "attribute": {"slug": page_type_product_single_reference_attribute.slug},
        "product": {"slug": product.slug},
    }
    expected_assigned_variant_attribute = {
        "attribute": {"slug": page_type_variant_single_reference_attribute.slug},
        "variant": {"sku": product_variant_list[0].sku},
    }
    expected_assigned_category_attribute = {
        "attribute": {"slug": page_type_category_single_reference_attribute.slug},
        "category": {"slug": categories[0].slug},
    }
    expected_assigned_collection_attribute = {
        "attribute": {"slug": page_type_collection_single_reference_attribute.slug},
        "collection": {"slug": collection.slug},
    }
    assert expected_assigned_page_attribute in assigned_attributes
    assert expected_assigned_product_attribute in assigned_attributes
    assert expected_assigned_variant_attribute in assigned_attributes
    assert expected_assigned_category_attribute in assigned_attributes
    assert expected_assigned_collection_attribute in assigned_attributes


def test_update_page_with_numeric_attribute(
    staff_api_client, permission_manage_pages, page, numeric_attribute
):
    # given
    query = UPDATE_PAGE_MUTATION

    page_type = page.page_type
    page_type.page_attributes.all().delete()
    page_type.page_attributes.add(numeric_attribute)

    numeric_value = 33.12
    numeric_name = str(numeric_value)

    variables = {
        "id": to_global_id_or_none(page),
        "input": {
            "attributes": [
                {
                    "id": to_global_id_or_none(numeric_attribute),
                    "numeric": numeric_value,
                }
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    attributes = data["page"]["attributes"]
    assert len(attributes) == 1
    assert attributes[0]["attribute"]["slug"] == numeric_attribute.slug
    assert len(attributes[0]["values"]) == 1
    assert attributes[0]["values"][0]["slug"] == f"{page.pk}_{numeric_attribute.pk}"
    assert attributes[0]["values"][0]["name"] == numeric_name

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": numeric_attribute.slug},
        "value": numeric_value,
    }
    assert expected_assigned_attribute in assigned_attributes

    assert numeric_attribute.values.filter(
        name=numeric_name,
        numeric=numeric_value,
    ).exists()


def test_page_update_reference_attribute_sets_search_index_dirty_in_product(
    staff_api_client,
    page,
    product,
    product_type_page_reference_attribute,
    permission_manage_pages,
):
    # given
    query = UPDATE_PAGE_MUTATION
    page_id = graphene.Node.to_global_id("Page", page.id)

    old_title = "Brand"
    page.title = old_title
    page.save(update_fields=["title"])

    # Set up page reference attribute
    attribute = product_type_page_reference_attribute
    attribute_value = AttributeValue.objects.create(
        attribute=attribute,
        name=page.title,
        slug=f"{page.pk}_{page.id}",
        reference_page=page,
    )
    product.product_type.product_attributes.add(attribute)
    associate_attribute_values_to_instance(product, {attribute.id: [attribute_value]})

    # Ensure product search index is initially clean
    product.search_index_dirty = False
    product.save(update_fields=["search_index_dirty"])
    update_products_search_vector([product.id])
    product.refresh_from_db()
    assert old_title.lower() in product.search_vector

    # when
    new_title = "Extra Brand"
    variables = {
        "id": page_id,
        "input": {"title": new_title},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )

    # then
    data = get_graphql_content(response)
    assert not data["data"]["pageUpdate"]["errors"]

    # Check that page was updated
    page.refresh_from_db()
    assert page.title == new_title

    # Check that product search_index_dirty flag was set to True
    product.refresh_from_db()
    update_products_search_vector([product.id])
    product.refresh_from_db()
    updated_search_vector = str(product.search_vector)

    # Verify search vector now contains the new page title
    assert "extra" in updated_search_vector
    # Verify search index dirty flag is reset
    assert product.search_index_dirty is False
