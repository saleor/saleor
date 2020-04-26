import math

import graphene
import pytest

from saleor.graphql.core.connection import CountableDjangoObjectType
from saleor.graphql.core.fields import FilterInputConnectionField

from .models import Book


class BookType(CountableDjangoObjectType):
    class Meta:
        model = Book


class Query(graphene.ObjectType):
    books = FilterInputConnectionField(BookType)


schema = graphene.Schema(query=Query)


@pytest.fixture
def books(db):
    books = [Book(name=f"Book{index}") for index in range(24)]
    return Book.objects.bulk_create(books)


QUERY_PAGINATION_TEST = """
    query BooksPaginationTest($first: Int, $last: Int, $after: String, $before: String){
        books(first: $first, last: $last, after: $after, before: $before) {
            edges {
                node {
                    name
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.mark.parametrize("page_size", [1, 5, 8, 25])
def test_pagination_forward(page_size, books):
    end_cursor = None
    has_next_page = True
    object_count = 0
    queries_count = 0
    while has_next_page:
        variables = {"first": page_size, "after": end_cursor}
        result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
        assert not result.errors
        content = result.data
        page_info = content["books"]["pageInfo"]
        has_next_page = page_info["hasNextPage"]
        end_cursor = page_info["endCursor"]
        object_count += len(content["books"]["edges"])
        queries_count += 1
    assert object_count == len(books)
    assert queries_count == math.ceil(len(books) / page_size)


@pytest.mark.parametrize("page_size", [1, 5, 8, 25])
def test_pagination_backward(page_size, books):
    start_cursor = None
    has_previous_page = True
    object_count = 0
    queries_count = 0
    while has_previous_page:
        variables = {"last": page_size, "before": start_cursor}
        result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
        assert not result.errors
        content = result.data
        page_info = content["books"]["pageInfo"]
        has_previous_page = page_info["hasPreviousPage"]
        start_cursor = page_info["startCursor"]
        object_count += len(content["books"]["edges"])
        queries_count += 1
    assert object_count == len(books)
    assert queries_count == math.ceil(len(books) / page_size)


def test_pagination_order(books):
    page_size = len(books)

    variables = {"first": page_size, "after": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    edges_forward = content["books"]["edges"]

    variables = {"last": page_size, "before": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    edges_backward = content["books"]["edges"]

    assert edges_forward == edges_backward


def test_pagination_previous_page_using_last(books):
    page_size = 5

    variables = {"first": page_size, "after": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    first_page_edges_forward = content["books"]["edges"]
    first_page_info_forward = content["books"]["pageInfo"]

    variables = {"first": page_size, "after": first_page_info_forward["endCursor"]}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    second_page_info = content["books"]["pageInfo"]

    variables = {"last": page_size, "before": second_page_info["startCursor"]}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    first_page_edges_backward = content["books"]["edges"]

    assert first_page_edges_forward == first_page_edges_backward


def test_pagination_forward_first_page_info(books):
    variables = {"first": 5, "after": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    page_info = content["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"] is False


def test_pagination_forward_middle_page_info(books):
    page_size = 5

    variables = {"first": page_size, "after": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    end_cursor = content["books"]["pageInfo"]["endCursor"]

    variables = {"first": page_size, "after": end_cursor}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    page_info = content["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"]


def test_pagination_forward_last_page_info(books):
    page_size = 20

    variables = {"first": page_size, "after": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    end_cursor = content["books"]["pageInfo"]["endCursor"]

    variables = {"first": page_size, "after": end_cursor}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    page_info = content["books"]["pageInfo"]
    assert page_info["hasNextPage"] is False
    assert page_info["hasPreviousPage"]


def test_pagination_backward_first_page_info(books):
    variables = {"last": 5, "before": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    page_info = content["books"]["pageInfo"]
    assert page_info["hasNextPage"] is False
    assert page_info["hasPreviousPage"]


def test_pagination_backward_middle_page_info(books):
    page_size = 5

    variables = {"last": 5, "before": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    start_cursor = content["books"]["pageInfo"]["startCursor"]

    variables = {"last": page_size, "before": start_cursor}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    page_info = content["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"]


def test_pagination_backward_last_page_info(books):
    page_size = 20

    variables = {"last": page_size, "before": None}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    start_cursor = content["books"]["pageInfo"]["startCursor"]

    variables = {"last": page_size, "before": start_cursor}
    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    content = result.data
    page_info = content["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"] is False
