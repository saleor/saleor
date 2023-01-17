from datetime import datetime, timedelta
from unittest import mock

import graphene
import pytz
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify
from freezegun import freeze_time

from .....page.error_codes import PageErrorCode
from .....page.models import Page, PageType
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_page_payload
from ....tests.utils import get_graphql_content

CREATE_PAGE_MUTATION = """
    mutation CreatePage(
        $input: PageCreateInput!
    ) {
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
def test_page_create_mutation(staff_api_client, permission_manage_pages, page_type):
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_attr_id = graphene.Node.to_global_id("Attribute", tag_attr.id)
    tag_value_name = tag_attr.values.first().name

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
            "slug": page_slug,
            "pageType": page_type_id,
            "attributes": [
                {"id": tag_attr_id, "values": [tag_value_name]},
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
    assert data["page"]["publishedAt"] == datetime.now(pytz.utc).isoformat()
    assert data["page"]["pageType"]["id"] == page_type_id
    values = (
        data["page"]["attributes"][0]["values"][0]["slug"],
        data["page"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert tag_value_slug in values


@freeze_time("2020-03-18 12:00:00")
def test_page_create_mutation_with_published_at_date(
    staff_api_client, permission_manage_pages, page_type
):
    page_slug = "test-slug"
    page_content = dummy_editorjs("test content", True)
    page_title = "test title"
    page_is_published = True
    published_at = datetime.now(pytz.utc).replace(microsecond=0) + timedelta(days=5)
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    # Default attributes defined in product_type fixture
    tag_attr = page_type.page_attributes.get(name="tag")
    tag_value_slug = tag_attr.values.first().slug
    tag_value_name = tag_attr.values.first().name
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
                {"id": tag_attr_id, "values": [tag_value_name]},
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
    assert tag_value_slug in values


@freeze_time("1914-06-28 10:50")
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
    expected_data = generate_page_payload(page, staff_api_client.user)

    mocked_webhook_trigger.assert_called_once_with(
        expected_data,
        WebhookEventAsyncType.PAGE_CREATED,
        [any_webhook],
        page,
        SimpleLazyObject(lambda: staff_api_client.user),
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

    # Default attributes defined in product_type fixture
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

    # Default attributes defined in product_type fixture
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
    site_settings,
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
    file_url = (
        f"http://{site_settings.site.domain}{settings.MEDIA_URL}{attr_value.file_url}"
    )

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

    page_file_attribute.refresh_from_db()
    assert page_file_attribute.values.count() == values_count + 1


def test_create_page_with_file_attribute_new_attribute_value(
    staff_api_client,
    permission_manage_pages,
    page_type,
    page_file_attribute,
    site_settings,
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
    file_url = f"http://{site_settings.site.domain}{settings.MEDIA_URL}{new_value}"
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

    page_type_page_reference_attribute.refresh_from_db()
    assert page_type_page_reference_attribute.values.count() == values_count + 1


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
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
    date_time_value = datetime.now(tz=pytz.utc)
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


@freeze_time(datetime(2020, 5, 5, 5, 5, 5, tzinfo=pytz.utc))
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
    date_time_value = datetime.now(tz=pytz.utc)
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

    file_attribute_id = graphene.Node.to_global_id(
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

    file_attribute_id = graphene.Node.to_global_id(
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

    file_attribute_id = graphene.Node.to_global_id(
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

    page_type_variant_reference_attribute.refresh_from_db()
    assert page_type_variant_reference_attribute.values.count() == values_count + 1
