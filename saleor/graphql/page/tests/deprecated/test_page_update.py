from datetime import datetime, timedelta

import graphene
import pytz

from .....page.error_codes import PageErrorCode
from .....page.models import Page
from ....tests.utils import get_graphql_content

UPDATE_PAGE_MUTATION = """
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
                isPublished
                publicationDate
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


def test_update_page_publication_date(
    staff_api_client, permission_manage_pages, page_type
):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "page_type": page_type,
    }
    page = Page.objects.create(**data)
    publication_date = datetime.now(pytz.utc) + timedelta(days=5)
    page_id = graphene.Node.to_global_id("Page", page.id)
    variables = {
        "id": page_id,
        "input": {
            "isPublished": True,
            "slug": page.slug,
            "publicationDate": publication_date,
        },
    }
    response = staff_api_client.post_graphql(
        UPDATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]

    assert not data["errors"]
    assert data["page"]["isPublished"] is True
    assert data["page"]["publicationDate"] == publication_date.date().isoformat()


def test_page_update_mutation_publication_date_and_published_at_provided(
    staff_api_client, permission_manage_pages, page_type
):
    """Test that setting publication date and time are mutually exclusive."""
    data = {
        "slug": "test-url",
        "title": "Test page",
        "page_type": page_type,
    }
    page = Page.objects.create(**data)
    published_at = datetime.now(pytz.utc) + timedelta(days=5)
    publication_date = datetime.now(pytz.utc) + timedelta(days=5)
    page_id = graphene.Node.to_global_id("Page", page.id)

    # test creating root page
    variables = {
        "id": page_id,
        "input": {
            "publishedAt": published_at,
            "publicationDate": publication_date,
        },
    }

    response = staff_api_client.post_graphql(
        UPDATE_PAGE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageUpdate"]
    assert not data["page"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "publicationDate"
    assert data["errors"][0]["code"] == PageErrorCode.INVALID.name
