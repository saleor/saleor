import base64
import math

import graphene
import pytest

from ....tests.models import Book
from ..connection import CountableConnection, create_connection_slice
from ..fields import ConnectionField


class BookType(graphene.ObjectType):
    name = graphene.String()


class BookTypeCountableConnection(CountableConnection):
    class Meta:
        node = BookType


class Query(graphene.ObjectType):
    books = ConnectionField(BookTypeCountableConnection)

    @staticmethod
    def resolve_books(_root, info, **kwargs):
        qs = Book.objects.all()
        return create_connection_slice(qs, info, kwargs, BookTypeCountableConnection)


schema = graphene.Schema(query=Query)


class ListQuery(graphene.ObjectType):
    """Query that resolves books from a list (simulates dataloader path)."""

    books = ConnectionField(BookTypeCountableConnection)

    @staticmethod
    def resolve_books(_root, info, **kwargs):
        items = [BookType(name=f"Book{i}") for i in range(24)]
        return create_connection_slice(items, info, kwargs, BookTypeCountableConnection)


list_schema = graphene.Schema(query=ListQuery)


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


def test_pagination_invalid_cursor(books):
    cursor = graphene.Node.to_global_id("BookType", -1)
    variables = {"first": 5, "after": cursor}

    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert str(result.errors[0]) == "Received cursor is invalid."


def test_pagination_invalid_cursor_and_valid_base64(books):
    cursor = base64.b64encode(str.encode(f"{['Test']}")).decode("utf-8")
    variables = {"first": 5, "after": cursor}

    result = schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    assert len(result.errors) == 1
    assert str(result.errors[0]) == "Received cursor is invalid."


QUERY_PAGINATION_WITH_FRAGMENTS = """
    fragment BookFragment on BookType {
        name
        __typename
    }

    fragment PageInfoFragment on PageInfo {
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
        __typename
    }

    fragment BookListFragment on BookTypeCountableConnection {
        pageInfo {
            ...PageInfoFragment
            __typename
        }
        edges {
            cursor
            node {
                ...BookFragment
                __typename
            }
            __typename
        }
        __typename
    }

    query BooksPaginationTest($first: Int, $last: Int, $after: String, $before: String){
        books(first: $first, last: $last, after: $after, before: $before) {
            ...BookListFragment
        }
    }
"""


def test_query_with_pagination_and_fragments(books):
    page_size = 10
    variables = {"first": page_size}

    result = schema.execute(QUERY_PAGINATION_WITH_FRAGMENTS, variables=variables)

    assert not result.errors
    content = result.data
    assert len(content["books"]["edges"]) == page_size


def test_query_with_pagination_and_fragments_no_first_or_last_raises_an_error(books):
    result = schema.execute(QUERY_PAGINATION_WITH_FRAGMENTS, variables={})

    assert result.errors
    assert len(result.errors) == 1
    expected_err_msg = (
        "You must provide a `first` or `last` value to properly paginate "
        "the `books` connection."
    )
    assert str(result.errors[0]) == expected_err_msg


QUERY_PAGINATION_WITH_INLINE_FRAGMENTS = """
    query BooksPaginationTest($first: Int, $last: Int, $after: String, $before: String){
        books(first: $first, last: $last, after: $after, before: $before) {
            ...on BookTypeCountableConnection {
                pageInfo {
                    ...on PageInfo {
                        endCursor
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        __typename
                    }
                    __typename
                }
                edges {
                    cursor
                    node {
                        ...on BookType {
                            name
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
                __typename
            }
        }
    }
"""


def test_query_with_pagination_and_inline_fragments(books):
    # given
    page_size = 10
    variables = {"first": page_size}

    # when
    result = schema.execute(QUERY_PAGINATION_WITH_INLINE_FRAGMENTS, variables=variables)

    # then
    assert not result.errors
    content = result.data
    assert len(content["books"]["edges"]) == page_size


def test_list_pagination_forward_first_page_info():
    """First page of forward list pagination has no previous page."""
    # given
    variables = {"first": 5}

    # when
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    # then
    assert not result.errors
    page_info = result.data["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"] is False


def test_list_pagination_forward_middle_page_info():
    """Middle page of forward list pagination has both previous and next pages."""
    # given
    variables = {"first": 5}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    end_cursor = result.data["books"]["pageInfo"]["endCursor"]

    # when
    variables = {"first": 5, "after": end_cursor}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    # then
    assert not result.errors
    page_info = result.data["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"]


def test_list_pagination_forward_last_page_info():
    """Last page of forward list pagination has previous page but no next."""
    # given
    variables = {"first": 20}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    end_cursor = result.data["books"]["pageInfo"]["endCursor"]

    # when
    variables = {"first": 20, "after": end_cursor}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    # then
    assert not result.errors
    page_info = result.data["books"]["pageInfo"]
    assert page_info["hasNextPage"] is False
    assert page_info["hasPreviousPage"]


def test_list_pagination_backward_first_page_info():
    """First page of backward list pagination has previous page (items before)."""
    # given
    variables = {"last": 5}

    # when
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    # then
    assert not result.errors
    page_info = result.data["books"]["pageInfo"]
    assert page_info["hasNextPage"] is False
    assert page_info["hasPreviousPage"]


def test_list_pagination_backward_middle_page_info():
    """Middle page of backward list pagination has both previous and next pages."""
    # given
    variables = {"last": 5}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    start_cursor = result.data["books"]["pageInfo"]["startCursor"]

    # when
    variables = {"last": 5, "before": start_cursor}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    # then
    assert not result.errors
    page_info = result.data["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"]


def test_list_pagination_backward_last_page_info():
    """Last page of backward list pagination has next page but no previous."""
    # given
    variables = {"last": 20}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)
    assert not result.errors
    start_cursor = result.data["books"]["pageInfo"]["startCursor"]

    # when
    variables = {"last": 20, "before": start_cursor}
    result = list_schema.execute(QUERY_PAGINATION_TEST, variables=variables)

    # then
    assert not result.errors
    page_info = result.data["books"]["pageInfo"]
    assert page_info["hasNextPage"]
    assert page_info["hasPreviousPage"] is False
