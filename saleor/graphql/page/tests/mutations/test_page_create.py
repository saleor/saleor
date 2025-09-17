import datetime
from functools import partial
from unittest import mock
from unittest.mock import ANY

import graphene
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....page.error_codes import PageErrorCode
from .....page.models import Page, PageType
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

CREATE_PAGE_MUTATION = """
mutation CreatePage($input: PageCreateInput!) {
  pageCreate(input: $input) {
    page {
      id
      title
      content
      slug
      isPublished
      publishedAt
      pageType {
        id
      }
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


@freeze_time("2020-03-18 12:00:00")
def test_page_create_mutation(
    staff_api_client, permission_manage_pages, page_type, numeric_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    page_type.page_attributes.add(numeric_attribute)

    # Default attributes defined in page_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")

    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)
    tag_value = tag_attr.values.first()

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attr.id)
    non_existent_attr_value = "New value"

    numeric_value = 42.1
    numeric_name = str(numeric_value)

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {"id": tag_attr_id, "values": [tag_value.name]},
                {"id": size_attr_id, "values": [non_existent_attr_value]},
                {
                    "id": to_global_id_or_none(numeric_attribute),
                    "values": [numeric_name],
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert (
        data["page"]["publishedAt"]
        == datetime.datetime.now(tz=datetime.UTC).isoformat()
    )
    assert data["page"]["pageType"]["id"] == page_type_id
    values = (
        data["page"]["attributes"][0]["values"][0]["slug"],
        data["page"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert tag_value.slug in values

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_size_assigned_attribute = {
        "attribute": {"slug": size_attr.slug},
        "choice": {
            "name": non_existent_attr_value,
            "slug": slugify(non_existent_attr_value),
        },
    }
    expected_tag_assigned_attribute = {
        "attribute": {"slug": tag_attr.slug},
        "choice": {
            "name": tag_value.name,
            "slug": tag_value.slug,
        },
    }
    assert expected_size_assigned_attribute in assigned_attributes
    assert expected_tag_assigned_attribute in assigned_attributes

    assert numeric_attribute.values.filter(
        name=numeric_name, numeric=numeric_value
    ).exists()


@freeze_time("2020-03-18 12:00:00")
def test_page_create_mutation_with_published_at_date(
    staff_api_client, permission_manage_pages, page_type
):
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    published_at = datetime.datetime.now(tz=datetime.UTC).replace(
        microsecond=0
    ) + datetime.timedelta(days=5)
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in page_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value = tag_attr.values.first()
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attr.id)
    non_existent_attr_value = "New value"

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "publishedAt": published_at,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {"id": tag_attr_id, "values": [tag_value.name]},
                {"id": size_attr_id, "values": [non_existent_attr_value]},
            ],
        }
    }

    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["publishedAt"] == published_at.isoformat()
    assert data["page"]["pageType"]["id"] == page_type_id
    values = (
        data["page"]["attributes"][0]["values"][0]["slug"],
        data["page"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert tag_value.slug in values

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_size_assigned_attribute = {
        "attribute": {"slug": size_attr.slug},
        "choice": {
            "name": non_existent_attr_value,
            "slug": slugify(non_existent_attr_value),
        },
    }
    expected_tag_assigned_attribute = {
        "attribute": {"slug": tag_attr.slug},
        "choice": {
            "name": tag_value.name,
            "slug": tag_value.slug,
        },
    }
    assert expected_size_assigned_attribute in assigned_attributes
    assert expected_tag_assigned_attribute in assigned_attributes


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_create_trigger_page_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_pages,
    page_type,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
        }
    }

    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    page = Page.objects.first()

    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PAGE_CREATED,
        [any_webhook],
        page,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )


def test_page_create_required_fields(
    staff_api_client, permission_manage_pages, page_type
):
    variables = {
        "input": {"pageType": graphene.Node.to_global_id("PageType", page_type.pk)}
    }
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageCreate"]["errors"]

    assert len(errors) == 2
    assert {error["field"] for error in errors} == {"title", "slug"}
    assert {error["code"] for error in errors} == {PageErrorCode.REQUIRED.name}


def test_create_default_slug(staff_api_client, permission_manage_pages, page_type):
    # test creating root page
    title = "Spanish inquisition"
    variables = {
        "input": {
            "title": title,
            "pageType": graphene.Node.to_global_id("PageType", page_type.pk),
        }
    }
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert not data["errors"]
    assert data["page"]["title"] == title
    assert data["page"]["slug"] == slugify(title)


def test_page_create_mutation_missing_required_attributes(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in page_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # Add second attribute
    size_attr = page_type.page_attributes.get(name="Page size")
    size_attr.value_required = True
    size_attr.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": tag_attr_id, "values": [tag_value_slug]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", size_attr.pk)
    ]


def test_page_create_mutation_empty_attribute_value(
    staff_api_client, permission_manage_pages, page_type
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in page_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": tag_attr_id, "values": ["  "]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["field"] == "attributes"
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["attributes"] == [
        graphene.Node.to_global_id("Attribute", tag_attr.pk)
    ]


def test_create_page_with_file_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_file_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)
    attr_value = page_file_attribute.values.first()

    values_count = page_file_attribute.values.count()
    file_url = f"https://example.com{settings.MEDIA_URL}{attr_value.file_url}"

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": file_attribute_id, "file": file_url}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    expected_attr_data = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": f"{attr_value.slug}-2",
                "name": attr_value.name,
                "file": {
                    "url": file_url,
                    "contentType": None,
                },
                "reference": None,
                "plainText": None,
                "date": None,
                "dateTime": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "file": {
            "url": file_url,
            "contentType": None,
        },
    }
    assert expected_assigned_attribute in assigned_attributes

    page_file_attribute.refresh_from_db()
    assert page_file_attribute.values.count() == values_count + 1


def test_create_page_with_file_attribute_new_attribute_value(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_file_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)
    new_value = "new_test_value.txt"
    file_url = f"https://example.com{settings.MEDIA_URL}{new_value}"
    new_value_content_type = "text/plain"

    values_count = page_file_attribute.values.count()

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {
                    "id": file_attribute_id,
                    "file": file_url,
                    "contentType": new_value_content_type,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    expected_attr_data = {
        "attribute": {"slug": page_file_attribute.slug},
        "values": [
            {
                "slug": slugify(new_value),
                "reference": None,
                "name": new_value,
                "file": {
                    "url": file_url,
                    "contentType": new_value_content_type,
                },
                "plainText": None,
                "date": None,
                "dateTime": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "file": {
            "url": file_url,
            "contentType": new_value_content_type,
        },
    }
    assert expected_assigned_attribute in assigned_attributes

    page_file_attribute.refresh_from_db()
    assert page_file_attribute.values.count() == values_count + 1


def test_create_page_with_file_attribute_not_required_no_file_url_given(
    staff_api_client, permission_manage_pages, page_type, page_file_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)

    page_file_attribute.value_required = False
    page_file_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": file_attribute_id, "file": ""}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    assert len(data["page"]["attributes"][0]["values"]) == 0

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_file_attribute.slug},
        "file": None,
    }
    assert expected_assigned_attribute in assigned_attributes


def test_create_page_with_file_attribute_required_no_file_url_given(
    staff_api_client, permission_manage_pages, page_type, page_file_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id("Attribute", page_file_attribute.pk)
    page_type.page_attributes.add(page_file_attribute)

    page_file_attribute.value_required = True
    page_file_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": file_attribute_id, "file": ""}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [file_attribute_id]


def test_create_page_with_page_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_reference_attribute,
    page,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)
    reference = graphene.Node.to_global_id("Page", page.pk)

    values_count = page_type_page_reference_attribute.values.count()

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": ref_attribute_id, "references": [reference]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{page.pk}",
                "file": None,
                "name": page.title,
                "reference": reference,
                "plainText": None,
                "date": None,
                "dateTime": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "pages": [{"slug": page.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count + 1


def test_create_page_with_reference_attributes_and_reference_types_defined(
    staff_api_client,
    page_type,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    page_type_variant_reference_attribute,
    page,
    product,
    variant,
    permission_manage_pages,
):
    # given
    page_type.page_attributes.clear()
    page_type.page_attributes.add(
        page_type_page_reference_attribute,
        page_type_product_reference_attribute,
        page_type_variant_reference_attribute,
    )

    page_type_page_reference_attribute.reference_page_types.add(page.page_type)
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
    page_ref = graphene.Node.to_global_id("Page", page.pk)
    product_ref = graphene.Node.to_global_id("Product", product.pk)
    variant_ref = graphene.Node.to_global_id("ProductVariant", variant.pk)

    page_title = "test title"
    page_slug = "test-slug"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {
        "input": {
            "title": page_title,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {"id": page_ref_attr_id, "references": [page_ref]},
                {"id": product_ref_attr_id, "references": [product_ref]},
                {"id": variant_ref_attr_id, "references": [variant_ref]},
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)["data"]["pageCreate"]

    assert not content["errors"]
    data = content["page"]
    assert data["title"] == page_title
    assert data["slug"] == page_slug
    page_id = data["id"]
    _, page_pk = graphene.Node.from_global_id(page_id)
    assert len(data["attributes"]) == len(variables["input"]["attributes"])
    expected_attributes_data = [
        {
            "attribute": {"slug": page_type_page_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{page_pk}_{page.id}",
                    "file": None,
                    "plainText": None,
                    "reference": page_ref,
                    "name": page.title,
                    "date": None,
                    "dateTime": None,
                }
            ],
        },
        {
            "attribute": {"slug": page_type_product_reference_attribute.slug},
            "values": [
                {
                    "slug": f"{page_pk}_{product.id}",
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
                    "slug": f"{page_pk}_{variant.id}",
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
    for attr_data in data["attributes"]:
        assert attr_data in expected_attributes_data

    assigned_attributes = data["assignedAttributes"]
    expected_page_ref_assigned_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "pages": [{"slug": page.slug}],
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


@freeze_time(datetime.datetime(2020, 5, 5, 5, 5, 5, tzinfo=datetime.UTC))
def test_create_page_with_date_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    date_attribute,
    page,
):
    # given
    page_type.page_attributes.add(date_attribute)

    page_title = "test title"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    date_attribute_id = graphene.Node.to_global_id("Attribute", date_attribute.id)
    date_time_value = datetime.datetime.now(tz=datetime.UTC)
    date_value = date_time_value.date()

    variables = {
        "input": {
            "title": page_title,
            "pageType": page_type_id,
            "attributes": [
                {"id": date_attribute_id, "date": date_value},
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["pageType"]["id"] == page_type_id
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attributes_data = {
        "attribute": {"slug": "release-date"},
        "values": [
            {
                "file": None,
                "reference": None,
                "plainText": None,
                "dateTime": None,
                "date": str(date_value),
                "name": str(date_value),
                "slug": f"{new_page_pk}_{date_attribute.id}",
            }
        ],
    }
    assert expected_attributes_data in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": date_attribute.slug},
        "date": str(date_value),
    }
    assert expected_assigned_attribute in assigned_attributes


@freeze_time(datetime.datetime(2020, 5, 5, 5, 5, 5, tzinfo=datetime.UTC))
def test_create_page_with_date_time_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    date_time_attribute,
    page,
):
    # given
    page_type.page_attributes.add(date_time_attribute)

    page_title = "test title"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    date_time_attribute_id = graphene.Node.to_global_id(
        "Attribute", date_time_attribute.id
    )
    date_time_value = datetime.datetime.now(tz=datetime.UTC)
    variables = {
        "input": {
            "title": page_title,
            "pageType": page_type_id,
            "attributes": [
                {"id": date_time_attribute_id, "dateTime": date_time_value},
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["pageType"]["id"] == page_type_id
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attributes_data = {
        "attribute": {"slug": "release-date-time"},
        "values": [
            {
                "file": None,
                "reference": None,
                "plainText": None,
                "dateTime": date_time_value.isoformat(),
                "date": None,
                "name": str(date_time_value),
                "slug": f"{new_page_pk}_{date_time_attribute.id}",
            }
        ],
    }

    assert expected_attributes_data in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": date_time_attribute.slug},
        "datetime": date_time_value.isoformat(),
    }
    assert expected_assigned_attribute in assigned_attributes


def test_create_page_with_plain_text_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    plain_text_attribute_page_type,
    page,
):
    # given
    page_type.page_attributes.add(plain_text_attribute_page_type)

    page_title = "test title"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    plain_text_attribute_id = graphene.Node.to_global_id(
        "Attribute", plain_text_attribute_page_type.id
    )
    text = "test plain text attribute content"

    variables = {
        "input": {
            "title": page_title,
            "pageType": page_type_id,
            "attributes": [
                {"id": plain_text_attribute_id, "plainText": text},
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["pageType"]["id"] == page_type_id
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attributes_data = {
        "attribute": {"slug": plain_text_attribute_page_type.slug},
        "values": [
            {
                "file": None,
                "reference": None,
                "dateTime": None,
                "date": None,
                "name": text,
                "plainText": text,
                "slug": f"{new_page_pk}_{plain_text_attribute_page_type.id}",
            }
        ],
    }
    assert expected_attributes_data in data["page"]["attributes"]

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": plain_text_attribute_page_type.slug},
        "plain_text": text,
    }
    assert expected_assigned_attribute in assigned_attributes


def test_create_page_with_page_reference_attribute_not_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    reference_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_type_page_reference_attribute.value_required = False
    page_type_page_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": reference_attribute_id}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    assert len(data["page"]["attributes"][0]["values"]) == 0

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_page_reference_attribute.slug},
        "pages": [],
    }
    assert expected_assigned_attribute in assigned_attributes


def test_create_page_with_page_reference_attribute_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    reference_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_type_page_reference_attribute.value_required = True
    page_type_page_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {
                    "id": reference_attribute_id,
                }
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [reference_attribute_id]


def test_create_page_with_reference_attributes_ref_not_in_available_choices(
    staff_api_client,
    page_type,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    page_type_variant_reference_attribute,
    page,
    product,
    variant,
    page_type_list,
    permission_manage_pages,
    product_type_with_variant_attributes,
):
    # given
    page_type.page_attributes.clear()
    page_type.page_attributes.add(
        page_type_page_reference_attribute,
        page_type_product_reference_attribute,
        page_type_variant_reference_attribute,
    )

    # assigned reference types that do not match product/page types of references
    # that are provided in the input
    page_type_page_reference_attribute.reference_page_types.add(page_type_list[1])
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
    page_ref = graphene.Node.to_global_id("Page", page.pk)
    product_ref = graphene.Node.to_global_id("Product", product.pk)
    variant_ref = graphene.Node.to_global_id("ProductVariant", variant.pk)

    page_title = "test title"
    page_slug = "test-slug"
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {
        "input": {
            "title": page_title,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {"id": page_ref_attr_id, "references": [page_ref]},
                {"id": product_ref_attr_id, "references": [product_ref]},
                {"id": variant_ref_attr_id, "references": [variant_ref]},
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)["data"]["pageCreate"]

    errors = content["errors"]
    assert not content["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.INVALID.name
    assert errors[0]["field"] == "attributes"
    assert set(errors[0]["attributes"]) == {
        page_ref_attr_id,
        product_ref_attr_id,
        variant_ref_attr_id,
    }


def test_create_page_with_product_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_product_reference_attribute,
    product,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_product_reference_attribute)
    reference = graphene.Node.to_global_id("Product", product.pk)

    values_count = page_type_product_reference_attribute.values.count()

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": ref_attribute_id, "references": [reference]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{product.pk}",
                "file": None,
                "name": product.name,
                "reference": reference,
                "plainText": None,
                "dateTime": None,
                "date": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "products": [{"slug": product.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_product_reference_attribute.refresh_from_db()
    assert page_type_product_reference_attribute.values.count() == values_count + 1


def test_create_page_with_product_reference_attribute_not_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_product_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    reference_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_product_reference_attribute)

    page_type_product_reference_attribute.value_required = False
    page_type_product_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": reference_attribute_id}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    assert len(data["page"]["attributes"][0]["values"]) == 0

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_product_reference_attribute.slug},
        "products": [],
    }
    assert expected_assigned_attribute in assigned_attributes


def test_create_page_with_product_reference_attribute_required_no_references_given(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_product_reference_attribute,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    file_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_product_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_product_reference_attribute)

    page_type_product_reference_attribute.value_required = True
    page_type_product_reference_attribute.save(update_fields=["value_required"])

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": file_attribute_id, "file": ""}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]
    assert not data["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.REQUIRED.name
    assert errors[0]["field"] == "attributes"
    assert errors[0]["attributes"] == [file_attribute_id]


def test_create_page_with_variant_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_variant_reference_attribute,
    variant,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_variant_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_variant_reference_attribute)
    reference = graphene.Node.to_global_id("ProductVariant", variant.pk)

    values_count = page_type_variant_reference_attribute.values.count()

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": ref_attribute_id, "references": [reference]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{variant.pk}",
                "file": None,
                "name": f"{variant.product.name}: {variant.name}",
                "reference": reference,
                "plainText": None,
                "dateTime": None,
                "date": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_variant_reference_attribute.slug},
        "variants": [{"sku": variant.sku}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_variant_reference_attribute.refresh_from_db()
    assert page_type_variant_reference_attribute.values.count() == values_count + 1


def test_create_page_with_category_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_category_reference_attribute,
    category,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_category_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_category_reference_attribute)
    reference = graphene.Node.to_global_id("Category", category.pk)

    values_count = page_type_category_reference_attribute.values.count()

    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": ref_attribute_id, "references": [reference]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_category_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{category.pk}",
                "file": None,
                "name": category.name,
                "reference": reference,
                "plainText": None,
                "dateTime": None,
                "date": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_category_reference_attribute.slug},
        "categories": [{"slug": category.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_category_reference_attribute.refresh_from_db()
    assert page_type_category_reference_attribute.values.count() == values_count + 1


def test_create_page_with_collection_reference_attribute(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_collection_reference_attribute,
    collection,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    ref_attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_collection_reference_attribute.pk
    )
    page_type.page_attributes.add(page_type_collection_reference_attribute)
    reference = graphene.Node.to_global_id("Collection", collection.pk)

    values_count = page_type_collection_reference_attribute.values.count()

    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [{"id": ref_attribute_id, "references": [reference]}],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    assert len(data["page"]["attributes"]) == 1
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attr_data = {
        "attribute": {"slug": page_type_collection_reference_attribute.slug},
        "values": [
            {
                "slug": f"{new_page_pk}_{collection.pk}",
                "file": None,
                "name": collection.name,
                "reference": reference,
                "plainText": None,
                "dateTime": None,
                "date": None,
            }
        ],
    }
    assert data["page"]["attributes"][0] == expected_attr_data
    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": page_type_collection_reference_attribute.slug},
        "collections": [{"slug": collection.slug}],
    }
    assert expected_assigned_attribute in assigned_attributes

    page_type_collection_reference_attribute.refresh_from_db()
    assert page_type_collection_reference_attribute.values.count() == values_count + 1


def test_create_page_with_single_reference_attributes(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_type_page_single_reference_attribute,
    page_type_product_single_reference_attribute,
    page_type_variant_single_reference_attribute,
    page_type_category_single_reference_attribute,
    page_type_collection_single_reference_attribute,
    collection,
    page,
    product,
    categories,
    product_variant_list,
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type = PageType.objects.create(
        name="Test page type 2", slug="test-page-type-2"
    )
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    page_type.page_attributes.add(
        page_type_page_single_reference_attribute,
        page_type_product_single_reference_attribute,
        page_type_variant_single_reference_attribute,
        page_type_category_single_reference_attribute,
        page_type_collection_single_reference_attribute,
    )
    references = [
        (page, page_type_page_single_reference_attribute, page.title),
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
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": attributes,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    errors = data["errors"]

    assert not errors
    assert data["page"]["title"] == page_title
    assert data["page"]["content"] == page_content
    assert data["page"]["slug"] == page_slug
    assert data["page"]["isPublished"] == page_is_published
    assert data["page"]["pageType"]["id"] == page_type_id
    attributes_data = data["page"]["attributes"]
    assert len(attributes_data) == len(references)
    page_id = data["page"]["id"]
    _, new_page_pk = graphene.Node.from_global_id(page_id)
    expected_attributes_data = [
        {
            "attribute": {
                "slug": attr.slug,
            },
            "values": [
                {
                    "slug": f"{new_page_pk}_{ref.id}",
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
        "page": {"slug": page.slug},
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


@freeze_time("2020-03-18 12:00:00")
def test_page_create_mutation_with_numeric_attribue(
    staff_api_client, permission_manage_pages, page_type, numeric_attribute
):
    # given
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)
    page_type.page_attributes.all().delete()
    page_type.page_attributes.add(numeric_attribute)

    numeric_value = 42.1
    numeric_name = str(numeric_value)

    # test creating root page
    variables = {
        "input": {
            "title": page_title,
            "content": page_content,
            "isPublished": page_is_published,
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {
                    "id": to_global_id_or_none(numeric_attribute),
                    "numeric": numeric_name,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageCreate"]
    assert data["errors"] == []

    assert len(data["page"]["attributes"]) == 1
    attribute = data["page"]["attributes"][0]
    assert attribute["attribute"]["slug"] == numeric_attribute.slug
    assert len(attribute["values"]) == 1
    assert (
        attribute["values"][0]["slug"]
        == f"{Page.objects.get().id}_{numeric_attribute.id}"
    )
    assert attribute["values"][0]["name"] == numeric_name

    assigned_attributes = data["page"]["assignedAttributes"]
    expected_assigned_attribute = {
        "attribute": {"slug": numeric_attribute.slug},
        "value": numeric_value,
    }
    assert expected_assigned_attribute in assigned_attributes

    assert numeric_attribute.values.filter(
        name=numeric_name, numeric=numeric_value
    ).exists()
