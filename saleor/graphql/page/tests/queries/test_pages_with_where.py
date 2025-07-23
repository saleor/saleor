import datetime

import graphene
import pytest

from .....attribute import AttributeEntityType, AttributeInputType, AttributeType
from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content

QUERY_PAGES_WITH_WHERE = """
    query ($where: PageWhereInput) {
        pages(first: 5, where:$where) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("where", "pages_count"),
    [
        ({"slug": {"eq": "test-url-1"}}, 1),
        ({"slug": {"oneOf": ["test-url-1", "test-url-2"]}}, 2),
    ],
)
def test_pages_with_where_slug(where, pages_count, staff_api_client, page_list):
    # given
    variables = {"where": where}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_count


def test_pages_with_where_page_type_eq(staff_api_client, page_type_list):
    # given
    page = Page.objects.first()
    assigned_page_type = page.page_type
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)

    pages_for_page_type = Page.objects.filter(page_type=assigned_page_type).count()
    assert PageType.objects.exclude(pk=assigned_page_type.pk).count() != 0
    assert pages_for_page_type != 0

    variables = {"where": {"pageType": {"eq": page_type_id}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_for_page_type


def test_pages_with_where_page_type_one_of(staff_api_client, page_type_list):
    # given
    page = Page.objects.first()
    assigned_page_type = page.page_type
    page_type_id = graphene.Node.to_global_id("PageType", page.page_type.pk)

    pages_for_page_type = Page.objects.filter(page_type=assigned_page_type).count()
    assert PageType.objects.exclude(pk=assigned_page_type.pk).count() != 0
    assert pages_for_page_type != 0

    variables = {"where": {"pageType": {"oneOf": [page_type_id]}}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == pages_for_page_type


@pytest.mark.parametrize(
    ("metadata", "expected_indexes"),
    [
        ({"key": "foo"}, [0, 1]),
        ({"key": "foo", "value": {"eq": "bar"}}, [0]),
        ({"key": "foo", "value": {"eq": "baz"}}, []),
        ({"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}, [0, 1]),
        ({"key": "notfound"}, []),
        ({"key": "foo", "value": {"eq": None}}, []),
        ({"key": "foo", "value": {"oneOf": []}}, []),
        (None, []),
    ],
)
def test_pages_with_where_metadata(
    metadata,
    expected_indexes,
    page_list,
    page_type,
    staff_api_client,
):
    # given
    page_list[0].metadata = {"foo": "bar"}
    page_list[1].metadata = {"foo": "zaz"}
    Page.objects.bulk_update(page_list, ["metadata"])
    page_list.append(
        Page.objects.create(
            title="Test page",
            slug="test-url-3",
            is_published=True,
            page_type=page_type,
            metadata={},
        )
    )

    variables = {"where": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages = content["data"]["pages"]["edges"]
    assert len(pages) == len(expected_indexes)
    ids = {node["node"]["id"] for node in pages}
    assert ids == {
        graphene.Node.to_global_id("Page", page_list[i].pk) for i in expected_indexes
    }


def test_pages_query_with_where_by_ids(
    staff_api_client, permission_manage_pages, page_list, page_list_unpublished
):
    # given
    query = QUERY_PAGES_WITH_WHERE

    page_ids = [
        graphene.Node.to_global_id("Page", page.pk)
        for page in [page_list[0], page_list_unpublished[-1]]
    ]
    variables = {"where": {"ids": page_ids}}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    # then
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["pages"]["totalCount"] == len(page_ids)


def test_pages_query_with_attribute_slug(
    staff_api_client, page_list, page_type, size_page_attribute
):
    # given
    page_type.page_attributes.add(size_page_attribute)
    page_attr_value = size_page_attribute.values.first()

    associate_attribute_values_to_instance(
        page_list[0], {size_page_attribute.pk: [page_attr_value]}
    )

    variables = {"where": {"attributes": [{"slug": size_page_attribute.slug}]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 1
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"slug": {"eq": "test-slug-1"}}}, 1),
        ({"value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}}}, 2),
        ({"slug": "size_page_attribute", "value": {"slug": {"eq": "test-slug-1"}}}, 1),
        (
            {
                "slug": "size_page_attribute",
                "value": {"slug": {"oneOf": ["test-slug-1", "test-slug-2"]}},
            },
            2,
        ),
    ],
)
def test_pages_query_with_attribute_value_slug(
    attribute_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
):
    # given
    size_page_attribute.slug = "size_page_attribute"
    size_page_attribute.save()

    page_type.page_attributes.add(size_page_attribute)

    attr_value_1 = size_page_attribute.values.first()
    attr_value_1.slug = "test-slug-1"
    attr_value_1.save()

    attr_value_2 = size_page_attribute.values.last()
    attr_value_2.slug = "test-slug-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        page_list[0], {size_page_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        page_list[1], {size_page_attribute.pk: [attr_value_2]}
    )

    variables = {"where": {"attributes": [attribute_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("attribute_input", "expected_count"),
    [
        ({"value": {"name": {"eq": "test-name-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}}}, 2),
        ({"slug": "size_page_attribute", "value": {"name": {"eq": "test-name-1"}}}, 1),
        (
            {
                "slug": "size_page_attribute",
                "value": {"name": {"oneOf": ["test-name-1", "test-name-2"]}},
            },
            2,
        ),
    ],
)
def test_pages_query_with_attribute_value_name(
    attribute_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
):
    # given
    size_page_attribute.slug = "size_page_attribute"
    size_page_attribute.save()

    page_type.page_attributes.add(size_page_attribute)

    attr_value_1 = size_page_attribute.values.first()
    attr_value_1.name = "test-name-1"
    attr_value_1.save()

    attr_value_2 = size_page_attribute.values.last()
    attr_value_2.name = "test-name-2"
    attr_value_2.save()

    associate_attribute_values_to_instance(
        page_list[0], {size_page_attribute.pk: [attr_value_1]}
    )

    associate_attribute_values_to_instance(
        page_list[1], {size_page_attribute.pk: [attr_value_2]}
    )

    variables = {"where": {"attributes": [attribute_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("numeric_input", "expected_count"),
    [
        ({"slug": "num-slug", "value": {"numeric": {"eq": 1.2}}}, 1),
        ({"slug": "num-slug", "value": {"numeric": {"oneOf": [1.2, 2]}}}, 2),
        (
            {"slug": "num-slug", "value": {"numeric": {"range": {"gte": 1, "lte": 2}}}},
            2,
        ),
        ({"slug": "num-slug", "value": {"name": {"eq": "1.2"}}}, 1),
        ({"slug": "num-slug", "value": {"slug": {"eq": "1.2"}}}, 1),
        ({"slug": "num-slug", "value": {"name": {"oneOf": ["1.2", "2"]}}}, 2),
        ({"slug": "num-slug", "value": {"slug": {"oneOf": ["1.2", "2"]}}}, 2),
        ({"value": {"numeric": {"eq": 1.2}}}, 1),
        ({"value": {"numeric": {"oneOf": [1.2, 2]}}}, 2),
        ({"value": {"numeric": {"range": {"gte": 1, "lte": 2}}}}, 2),
        ({"value": {"numeric": {"range": {"gte": 1}}}}, 3),
        ({"value": {"name": {"eq": "1.2"}}}, 1),
        ({"value": {"slug": {"eq": "1.2"}}}, 1),
        ({"value": {"name": {"oneOf": ["1.2", "2"]}}}, 2),
        ({"value": {"slug": {"oneOf": ["1.2", "2"]}}}, 2),
    ],
)
def test_pages_query_with_attribute_value_numeric(
    numeric_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    numeric_attribute_without_unit,
    numeric_attribute,
):
    # given
    numeric_attribute_without_unit.slug = "num-slug"
    numeric_attribute_without_unit.type = "PAGE_TYPE"
    numeric_attribute_without_unit.save()

    page_type.page_attributes.add(numeric_attribute_without_unit)
    page_type.page_attributes.add(numeric_attribute)

    attr_value_1 = numeric_attribute_without_unit.values.first()
    attr_value_1.name = "1.2"
    attr_value_1.slug = "1.2"
    attr_value_1.numeric = 1.2
    attr_value_1.save()

    attr_value_2 = numeric_attribute_without_unit.values.last()
    attr_value_2.name = "2"
    attr_value_2.slug = "2"
    attr_value_2.numeric = 2
    attr_value_2.save()

    second_attr_value = numeric_attribute.values.first()

    associate_attribute_values_to_instance(
        page_list[0],
        {
            numeric_attribute_without_unit.pk: [attr_value_1],
        },
    )

    associate_attribute_values_to_instance(
        page_list[1], {numeric_attribute_without_unit.pk: [attr_value_2]}
    )
    associate_attribute_values_to_instance(
        page_list[2], {numeric_attribute.pk: [second_attr_value]}
    )

    variables = {"where": {"attributes": [numeric_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("date_input", "expected_count"),
    [
        ({"slug": "date", "value": {"date": {"gte": "2021-01-01"}}}, 1),
        ({"slug": "date", "value": {"name": {"eq": "date-name-1"}}}, 1),
        ({"slug": "date", "value": {"slug": {"eq": "date-slug-1"}}}, 1),
        (
            {
                "slug": "date",
                "value": {"name": {"oneOf": ["date-name-1", "date-name-2"]}},
            },
            1,
        ),
        (
            {
                "slug": "date",
                "value": {"slug": {"oneOf": ["date-slug-1", "date-slug-2"]}},
            },
            1,
        ),
        (
            {
                "slug": "date",
                "value": {"date": {"gte": "2021-01-02", "lte": "2021-01-03"}},
            },
            1,
        ),
        ({"value": {"date": {"gte": "2021-01-01"}}}, 2),
        ({"value": {"name": {"eq": "date-name-1"}}}, 1),
        ({"value": {"slug": {"eq": "date-slug-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["date-name-1", "date-name-2"]}}}, 2),
        ({"value": {"slug": {"oneOf": ["date-slug-1", "date-slug-2"]}}}, 2),
        ({"value": {"date": {"gte": "2021-01-01", "lte": "2021-01-02"}}}, 1),
    ],
)
def test_pages_query_with_attribute_value_date(
    date_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    date_attribute,
):
    # given
    date_attribute.type = "PAGE_TYPE"
    date_attribute.slug = "date"
    date_attribute.save()

    second_date_attribute = Attribute.objects.create(
        slug="second_date",
        name="Second date",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.DATE,
    )
    page_type.page_attributes.add(date_attribute)
    page_type.page_attributes.add(second_date_attribute)

    attr_value_1 = date_attribute.values.first()
    attr_value_1.date_time = datetime.datetime(2021, 1, 3, tzinfo=datetime.UTC)
    attr_value_1.name = "date-name-1"
    attr_value_1.slug = "date-slug-1"
    attr_value_1.save()

    associate_attribute_values_to_instance(
        page_list[0], {date_attribute.pk: [attr_value_1]}
    )

    second_attr_value = second_date_attribute.values.create(
        date_time=datetime.datetime(2021, 1, 2, tzinfo=datetime.UTC),
        name="date-name-2",
        slug="date-slug-2",
    )

    associate_attribute_values_to_instance(
        page_list[1], {second_date_attribute.pk: [second_attr_value]}
    )

    variables = {"where": {"attributes": [date_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("date_time_input", "expected_count"),
    [
        ({"slug": "dt", "value": {"name": {"eq": "datetime-name-1"}}}, 1),
        ({"slug": "dt", "value": {"slug": {"eq": "datetime-slug-1"}}}, 1),
        (
            {
                "slug": "dt",
                "value": {"name": {"oneOf": ["datetime-name-1", "datetime-name-2"]}},
            },
            2,
        ),
        (
            {
                "slug": "dt",
                "value": {"slug": {"oneOf": ["datetime-slug-1", "datetime-slug-2"]}},
            },
            2,
        ),
        ({"slug": "dt", "value": {"dateTime": {"gte": "2021-01-01T00:00:00Z"}}}, 2),
        (
            {
                "slug": "dt",
                "value": {
                    "dateTime": {
                        "gte": "2021-01-01T00:00:00Z",
                        "lte": "2021-01-02T00:00:00Z",
                    }
                },
            },
            1,
        ),
        ({"value": {"name": {"eq": "datetime-name-1"}}}, 1),
        ({"value": {"slug": {"eq": "datetime-slug-1"}}}, 1),
        ({"value": {"name": {"oneOf": ["datetime-name-1", "datetime-name-2"]}}}, 2),
        ({"value": {"slug": {"oneOf": ["datetime-slug-1", "datetime-slug-2"]}}}, 2),
        ({"value": {"dateTime": {"gte": "2021-01-01T00:00:00Z"}}}, 3),
        (
            {
                "value": {
                    "dateTime": {
                        "gte": "2021-01-01T00:00:00Z",
                        "lte": "2021-01-02T00:00:00Z",
                    }
                }
            },
            2,
        ),
    ],
)
def test_pages_query_with_attribute_value_date_time(
    date_time_input,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    date_time_attribute,
):
    # given
    date_time_attribute.slug = "dt"
    date_time_attribute.type = "PAGE_TYPE"
    date_time_attribute.save()

    second_date_attribute = Attribute.objects.create(
        slug="second_dt",
        name="Second dt",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.DATE_TIME,
    )

    page_type.page_attributes.add(date_time_attribute)
    page_type.page_attributes.add(second_date_attribute)

    attr_value_1 = date_time_attribute.values.first()
    attr_value_1.date_time = datetime.datetime(2021, 1, 3, tzinfo=datetime.UTC)
    attr_value_1.name = "datetime-name-1"
    attr_value_1.slug = "datetime-slug-1"
    attr_value_1.save()

    associate_attribute_values_to_instance(
        page_list[0], {date_time_attribute.pk: [attr_value_1]}
    )

    second_attr_value = date_time_attribute.values.last()
    second_attr_value.date_time = datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC)
    second_attr_value.name = "datetime-name-2"
    second_attr_value.slug = "datetime-slug-2"
    second_attr_value.save()

    associate_attribute_values_to_instance(
        page_list[1], {date_time_attribute.pk: [second_attr_value]}
    )

    value_for_second_attr = second_date_attribute.values.create(
        date_time=datetime.datetime(2021, 1, 1, tzinfo=datetime.UTC),
        name="second-datetime-name",
        slug="second-datetime-slug",
    )

    associate_attribute_values_to_instance(
        page_list[2], {second_date_attribute.pk: [value_for_second_attr]}
    )

    variables = {"where": {"attributes": [date_time_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    "boolean_input",
    [
        {"value": {"boolean": True}},
        {"value": {"name": {"eq": "True-name"}}},
        {"value": {"slug": {"eq": "true_slug"}}},
        {"value": {"name": {"oneOf": ["True-name", "True-name-2"]}}},
        {"value": {"slug": {"oneOf": ["true_slug"]}}},
        {"slug": "b_s", "value": {"boolean": True}},
        {"slug": "b_s", "value": {"name": {"eq": "True-name"}}},
        {"slug": "b_s", "value": {"slug": {"eq": "true_slug"}}},
        {"slug": "b_s", "value": {"name": {"oneOf": ["True-name", "True-name-2"]}}},
        {"slug": "b_s", "value": {"slug": {"oneOf": ["true_slug"]}}},
    ],
)
def test_pages_query_with_attribute_value_boolean(
    boolean_input,
    staff_api_client,
    page_list,
    page_type,
    boolean_attribute,
):
    # given
    boolean_attribute.slug = "b_s"
    boolean_attribute.type = "PAGE_TYPE"
    boolean_attribute.save()

    second_attribute = Attribute.objects.create(
        slug="s_boolean",
        name="Boolean",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.BOOLEAN,
    )

    page_type.page_attributes.add(boolean_attribute)
    page_type.page_attributes.add(second_attribute)

    true_value = boolean_attribute.values.filter(boolean=True).first()
    true_value.name = "True-name"
    true_value.slug = "true_slug"
    true_value.save()

    associate_attribute_values_to_instance(
        page_list[0], {boolean_attribute.pk: [true_value]}
    )

    value_for_second_attr = AttributeValue.objects.create(
        attribute=second_attribute,
        name=f"{second_attribute.name}: Yes",
        slug=f"{second_attribute.id}_false",
        boolean=False,
    )
    associate_attribute_values_to_instance(
        page_list[1], {second_attribute.pk: [value_for_second_attr]}
    )

    variables = {"where": {"attributes": [boolean_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 1
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_pages_query_with_attr_slug_and_attribute_value_reference_to_pages(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    page_type.page_attributes.add(page_type_page_reference_attribute)

    reference_page_1_slug = "referenced-page-1"
    reference_page_2_slug = "referenced-page-2"
    referenced_page_1, referenced_page_2 = Page.objects.bulk_create(
        [
            Page(
                title="Referenced Page 1",
                slug=reference_page_1_slug,
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Referenced Page 2",
                slug=reference_page_2_slug,
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                name=f"Page {referenced_page_1.pk}",
                slug=f"page-{referenced_page_1.pk}",
                reference_page=referenced_page_1,
            ),
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                name=f"Page {referenced_page_2.pk}",
                slug=f"page-{referenced_page_2.pk}",
                reference_page=referenced_page_2,
            ),
        ]
    )
    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {page_type_page_reference_attribute.pk: [attribute_value_1, attribute_value_2]},
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {page_type_page_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "page-reference",
                    "value": {
                        "reference": {
                            "pageSlugs": {
                                filter_type: [
                                    reference_page_1_slug,
                                    reference_page_2_slug,
                                ]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_pages_query_with_attribute_value_reference_to_pages(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    second_page_reference_attribute = Attribute.objects.create(
        slug="second-page-reference",
        name="Page reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PAGE,
    )
    page_type.page_attributes.add(page_type_page_reference_attribute)
    page_type.page_attributes.add(second_page_reference_attribute)

    reference_1 = "referenced-page-1"
    reference_2 = "referenced-page-2"
    referenced_page_1, referenced_page_2 = Page.objects.bulk_create(
        [
            Page(
                title="Referenced Page 1",
                slug=reference_1,
                page_type=page_type,
                is_published=True,
            ),
            Page(
                title="Referenced Page 2",
                slug=reference_2,
                page_type=page_type,
                is_published=True,
            ),
        ]
    )

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                name=f"Page {referenced_page_1.pk}",
                slug=f"page-{referenced_page_1.pk}",
                reference_page=referenced_page_1,
            ),
            AttributeValue(
                attribute=second_page_reference_attribute,
                name=f"Page {referenced_page_2.pk}",
                slug=f"page-{referenced_page_2.pk}",
                reference_page=referenced_page_2,
            ),
        ]
    )
    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_page_reference_attribute.pk: [attribute_value_1],
            second_page_reference_attribute.pk: [attribute_value_2],
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {second_page_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "pageSlugs": {filter_type: [reference_1, reference_2]}
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"),
    [("containsAny", 2), ("containsAll", 1)],
)
def test_pages_query_with_attr_slug_and_attribute_value_reference_to_products(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_product_reference_attribute,
    product_list,
):
    # given
    page_type.page_attributes.add(page_type_product_reference_attribute)

    first_product = product_list[0]
    second_product = product_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {first_product.pk}",
                slug=f"product-{first_product.pk}",
                reference_product=first_product,
            ),
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {second_product.pk}",
                slug=f"product-{second_product.pk}",
                reference_product=second_product,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_product_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {page_type_product_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "product-reference",
                    "value": {
                        "reference": {
                            "productSlugs": {
                                filter_type: [first_product.slug, second_product.slug]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"),
    [("containsAny", 2), ("containsAll", 1)],
)
def test_pages_query_with_attribute_value_reference_to_products(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_product_reference_attribute,
    product_list,
):
    # given
    second_product_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )

    page_type.page_attributes.add(page_type_product_reference_attribute)
    page_type.page_attributes.add(second_product_reference_attribute)

    first_product = product_list[0]
    second_product = product_list[1]

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {first_product.pk}",
                slug=f"product-{first_product.pk}",
                reference_product=first_product,
            ),
            AttributeValue(
                attribute=second_product_reference_attribute,
                name=f"Product {second_product.pk}",
                slug=f"product-{second_product.pk}",
                reference_product=second_product,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_product_reference_attribute.pk: [
                attribute_value_1,
            ],
            second_product_reference_attribute.pk: [attribute_value_2],
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {second_product_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "productSlugs": {
                                filter_type: [first_product.slug, second_product.slug]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_pages_query_with_attribute_value_reference_to_product_variants(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_variant_reference_attribute,
    product_variant_list,
):
    # given
    page_type.page_attributes.add(page_type_variant_reference_attribute)
    second_variant_reference_attribute = Attribute.objects.create(
        slug="second-product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT_VARIANT,
    )

    first_variant_sku = "test-variant-1"
    second_variant_sku = "test-variant-2"

    first_variant = product_variant_list[0]
    first_variant.sku = first_variant_sku
    first_variant.save()

    second_variant = product_variant_list[1]
    second_variant.sku = second_variant_sku
    second_variant.save()

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_variant_reference_attribute,
                name=f"Variant {first_variant.pk}",
                slug=f"variant-{first_variant.pk}",
                reference_variant=first_variant,
            ),
            AttributeValue(
                attribute=second_variant_reference_attribute,
                name=f"Variant {second_variant.pk}",
                slug=f"variant-{second_variant.pk}",
                reference_variant=second_variant,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_variant_reference_attribute.pk: [attribute_value_1],
            second_variant_reference_attribute.pk: [attribute_value_2],
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {second_variant_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "productVariantSkus": {
                                filter_type: [
                                    first_variant_sku,
                                    second_variant_sku,
                                ]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 2), ("containsAll", 1)]
)
def test_pages_query_with_attr_slug_and_attribute_value_reference_to_product_variants(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_variant_reference_attribute,
    product_variant_list,
):
    # given
    page_type.page_attributes.add(page_type_variant_reference_attribute)

    first_variant_sku = "test-variant-1"
    second_variant_sku = "test-variant-2"

    first_variant = product_variant_list[0]
    first_variant.sku = first_variant_sku
    first_variant.save()

    second_variant = product_variant_list[1]
    second_variant.sku = second_variant_sku
    second_variant.save()

    attribute_value_1, attribute_value_2 = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_variant_reference_attribute,
                name=f"Variant {first_variant.pk}",
                slug=f"variant-{first_variant.pk}",
                reference_variant=first_variant,
            ),
            AttributeValue(
                attribute=page_type_variant_reference_attribute,
                name=f"Variant {second_variant.pk}",
                slug=f"variant-{second_variant.pk}",
                reference_variant=second_variant,
            ),
        ]
    )

    page_with_both_references = page_list[0]
    associate_attribute_values_to_instance(
        page_with_both_references,
        {
            page_type_variant_reference_attribute.pk: [
                attribute_value_1,
                attribute_value_2,
            ]
        },
    )

    page_with_single_reference = page_list[1]
    associate_attribute_values_to_instance(
        page_with_single_reference,
        {page_type_variant_reference_attribute.pk: [attribute_value_2]},
    )

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "variant-reference",
                    "value": {
                        "reference": {
                            "productVariantSkus": {
                                filter_type: [
                                    first_variant_sku,
                                    second_variant_sku,
                                ]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_pages_query_with_attribute_value_referenced_ids(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    page_type_variant_reference_attribute,
    product,
    variant,
):
    # given
    page_type.page_attributes.add(
        page_type_page_reference_attribute,
    )

    referenced_page = Page.objects.create(
        title="Referenced Page",
        slug="referenced-page",
        page_type=page_type,
        is_published=True,
    )

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=page_type_page_reference_attribute,
                    name=f"Page {referenced_page.pk}",
                    slug=f"page-{referenced_page.pk}",
                    reference_page=referenced_page,
                ),
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {product.pk}",
                    slug=f"product-{product.pk}",
                    reference_product=product,
                ),
                AttributeValue(
                    attribute=page_type_variant_reference_attribute,
                    name=f"variant {variant.pk}",
                    slug=f"variant-{variant.pk}",
                    reference_variant=variant,
                ),
            ]
        )
    )
    fist_page_with_all_ids = page_list[0]
    second_page_with_all_ids = page_list[1]
    page_with_single_id = page_list[2]
    associate_attribute_values_to_instance(
        fist_page_with_all_ids,
        {
            page_type_page_reference_attribute.pk: [first_attr_value],
            page_type_product_reference_attribute.pk: [second_attr_value],
            page_type_variant_reference_attribute.pk: [third_attr_value],
        },
    )

    associate_attribute_values_to_instance(
        second_page_with_all_ids,
        {
            page_type_page_reference_attribute.pk: [first_attr_value],
            page_type_product_reference_attribute.pk: [second_attr_value],
            page_type_variant_reference_attribute.pk: [third_attr_value],
        },
    )

    associate_attribute_values_to_instance(
        page_with_single_id,
        {page_type_page_reference_attribute.pk: [first_attr_value]},
    )

    referenced_first_id = to_global_id_or_none(referenced_page)
    referenced_second_id = to_global_id_or_none(product)
    referenced_third_id = to_global_id_or_none(variant)

    variables = {
        "where": {
            "attributes": [
                {
                    "value": {
                        "reference": {
                            "referencedIds": {
                                filter_type: [
                                    referenced_first_id,
                                    referenced_second_id,
                                    referenced_third_id,
                                ]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(page_list) > len(pages_nodes)
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_pages_query_with_attr_slug_and_attribute_value_referenced_page_ids(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_page_reference_attribute,
):
    # given
    page_type.page_attributes.add(
        page_type_page_reference_attribute,
    )

    referenced_first_page, referenced_second_page, referenced_third_page = (
        Page.objects.bulk_create(
            [
                Page(
                    title="Referenced Page",
                    slug="referenced-page",
                    page_type=page_type,
                    is_published=True,
                ),
                Page(
                    title="Referenced Page",
                    slug="referenced-page2",
                    page_type=page_type,
                    is_published=True,
                ),
                Page(
                    title="Referenced Page",
                    slug="referenced-page3",
                    page_type=page_type,
                    is_published=True,
                ),
            ]
        )
    )

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=page_type_page_reference_attribute,
                    name=f"Page {referenced_first_page.pk}",
                    slug=f"page-{referenced_first_page.pk}",
                    reference_page=referenced_first_page,
                ),
                AttributeValue(
                    attribute=page_type_page_reference_attribute,
                    name=f"Page {referenced_second_page.pk}",
                    slug=f"page-{referenced_second_page.pk}",
                    reference_page=referenced_second_page,
                ),
                AttributeValue(
                    attribute=page_type_page_reference_attribute,
                    name=f"Page {referenced_third_page.pk}",
                    slug=f"page-{referenced_third_page.pk}",
                    reference_page=referenced_third_page,
                ),
            ]
        )
    )
    fist_page_with_all_ids = page_list[0]
    second_page_with_all_ids = page_list[1]
    page_with_single_id = page_list[2]
    associate_attribute_values_to_instance(
        fist_page_with_all_ids,
        {
            page_type_page_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_page_with_all_ids,
        {
            page_type_page_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        page_with_single_id,
        {page_type_page_reference_attribute.pk: [first_attr_value]},
    )

    referenced_first_global_id = to_global_id_or_none(referenced_first_page)
    referenced_second_global_id = to_global_id_or_none(referenced_second_page)
    referenced_third_global_id = to_global_id_or_none(referenced_third_page)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": page_type_page_reference_attribute.slug,
                    "value": {
                        "reference": {
                            "referencedIds": {
                                filter_type: [
                                    referenced_first_global_id,
                                    referenced_second_global_id,
                                    referenced_third_global_id,
                                ]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(page_list) > len(pages_nodes)
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_pages_query_with_attr_slug_attribute_value_referenced_variant_ids(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_variant_reference_attribute,
    product_variant_list,
):
    # given
    page_type.page_attributes.add(
        page_type_variant_reference_attribute,
    )

    first_variant = product_variant_list[0]
    second_variant = product_variant_list[1]
    third_variant = product_variant_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=page_type_variant_reference_attribute,
                    name=f"Variant {first_variant.pk}",
                    slug=f"variant-{first_variant.pk}",
                    reference_variant=first_variant,
                ),
                AttributeValue(
                    attribute=page_type_variant_reference_attribute,
                    name=f"Variant {second_variant.pk}",
                    slug=f"variant-{second_variant.pk}",
                    reference_variant=second_variant,
                ),
                AttributeValue(
                    attribute=page_type_variant_reference_attribute,
                    name=f"Variant {third_variant.pk}",
                    slug=f"variant-{third_variant.pk}",
                    reference_variant=third_variant,
                ),
            ]
        )
    )
    fist_page_with_all_ids = page_list[0]
    second_page_with_all_ids = page_list[1]
    page_with_single_id = page_list[2]
    associate_attribute_values_to_instance(
        fist_page_with_all_ids,
        {
            page_type_variant_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_page_with_all_ids,
        {
            page_type_variant_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        page_with_single_id,
        {page_type_variant_reference_attribute.pk: [first_attr_value]},
    )
    referenced_first_global_id = to_global_id_or_none(first_variant)
    referenced_second_global_id = to_global_id_or_none(second_variant)
    referenced_third_global_id = to_global_id_or_none(third_variant)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": page_type_variant_reference_attribute.slug,
                    "value": {
                        "reference": {
                            "referencedIds": {
                                filter_type: [
                                    referenced_first_global_id,
                                    referenced_second_global_id,
                                    referenced_third_global_id,
                                ]
                            }
                        }
                    },
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(page_list) > len(pages_nodes)
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    ("filter_type", "expected_count"), [("containsAny", 3), ("containsAll", 2)]
)
def test_pages_query_with_attr_slug_and_attribute_value_referenced_product_ids(
    filter_type,
    expected_count,
    staff_api_client,
    page_list,
    page_type,
    page_type_product_reference_attribute,
    product_list,
):
    # given
    page_type.page_attributes.add(
        page_type_product_reference_attribute,
    )
    first_product = product_list[0]
    second_product = product_list[1]
    third_product = product_list[2]

    first_attr_value, second_attr_value, third_attr_value = (
        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {first_product.pk}",
                    slug=f"Product-{first_product.pk}",
                    reference_product=first_product,
                ),
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {second_product.pk}",
                    slug=f"product-{second_product.pk}",
                    reference_product=second_product,
                ),
                AttributeValue(
                    attribute=page_type_product_reference_attribute,
                    name=f"Product {third_product.pk}",
                    slug=f"Product-{third_product.pk}",
                    reference_product=third_product,
                ),
            ]
        )
    )
    fist_page_with_all_ids = page_list[0]
    second_page_with_all_ids = page_list[1]
    page_with_single_id = page_list[2]
    associate_attribute_values_to_instance(
        fist_page_with_all_ids,
        {
            page_type_product_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        second_page_with_all_ids,
        {
            page_type_product_reference_attribute.pk: [
                first_attr_value,
                second_attr_value,
                third_attr_value,
            ],
        },
    )

    associate_attribute_values_to_instance(
        page_with_single_id,
        {
            page_type_product_reference_attribute.pk: [
                first_attr_value,
            ],
        },
    )
    referenced_first_global_id = to_global_id_or_none(first_product)
    referenced_second_global_id = to_global_id_or_none(second_product)
    referenced_third_global_id = to_global_id_or_none(third_product)

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": page_type_product_reference_attribute.slug,
                    "value": {
                        "reference": {
                            "referencedIds": {
                                filter_type: [
                                    referenced_first_global_id,
                                    referenced_second_global_id,
                                    referenced_third_global_id,
                                ]
                            }
                        }
                    },
                },
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(page_list) > len(pages_nodes)
    assert len(pages_nodes) == expected_count


@pytest.mark.parametrize(
    "attribute_value_filter",
    [{"numeric": None}, {"name": None}, {"slug": None}, {"boolean": False}],
)
def test_pages_query_failed_filter_validation_for_numeric_with_slug_input(
    attribute_value_filter, staff_api_client, numeric_attribute_without_unit, page_type
):
    # given
    attr_slug_input = "numeric"
    numeric_attribute_without_unit.slug = attr_slug_input
    numeric_attribute_without_unit.save()

    page_type.page_attributes.add(numeric_attribute_without_unit)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [{"boolean": None}, {"name": None}, {"slug": None}, {"numeric": {"eq": 1.2}}],
)
def test_pages_query_failed_filter_validation_for_boolean_with_slug_input(
    attribute_value_filter, staff_api_client, boolean_attribute, page_type
):
    # given
    attr_slug_input = "boolean"
    boolean_attribute.slug = attr_slug_input
    boolean_attribute.save()

    page_type.page_attributes.add(boolean_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"dateTime": None},
        {"name": None},
        {"slug": None},
        {"numeric": {"eq": 1.2}},
        {"reference": {"referencedIds": {"containsAll": ["global-id-1"]}}},
    ],
)
def test_pages_query_failed_filter_validation_for_date_attribute_with_slug_input(
    attribute_value_filter, staff_api_client, date_attribute, page_type
):
    # given
    attr_slug_input = "date"
    date_attribute.slug = attr_slug_input
    date_attribute.save()

    page_type.page_attributes.add(date_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"dateTime": None},
        {"name": None},
        {"slug": None},
        {"numeric": {"eq": 1.2}},
        {"date": None},
        {"reference": {"referencedIds": {"containsAll": ["global-id-1"]}}},
    ],
)
def test_pages_query_failed_filter_validation_for_datetime_attribute_with_slug_input(
    attribute_value_filter, staff_api_client, date_time_attribute, page_type
):
    # given
    attr_slug_input = "date_time"
    date_time_attribute.slug = attr_slug_input
    date_time_attribute.save()

    page_type.page_attributes.add(date_time_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"slug": None, "value": None},
        {"slug": None, "value": {"name": {"eq": "name"}}},
    ],
)
def test_pages_query_failed_filter_validation_null_in_input(
    attribute_value_filter,
    staff_api_client,
):
    # given
    variables = {"where": {"attributes": [attribute_value_filter]}}
    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"slug": None},
        {"name": None},
        {
            "slug": {"eq": "true_slug"},
            "name": {"eq": "name"},
        },
        {
            "slug": {"oneOf": ["true_slug"]},
            "name": {"oneOf": ["name"]},
        },
    ],
)
def test_pages_query_failed_filter_validation_for_basic_value_fields_with_attr_slug(
    attribute_value_filter,
    staff_api_client,
):
    # given
    attr_slug_input = "page-size"

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        }
    }
    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


def test_pages_query_failed_filter_validation_for_duplicated_attr_slug(
    staff_api_client,
):
    # given
    attr_slug_input = "page-size"

    variables = {
        "where": {
            "attributes": [
                {"slug": attr_slug_input},
                {"slug": attr_slug_input},
            ]
        }
    }
    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {},
        {"reference": {}},
        {"reference": None},
        {"reference": {"referencedIds": {"containsAll": []}}},
        {"reference": {"pageSlugs": {"containsAll": []}}},
        {"reference": {"productSlugs": {"containsAll": []}}},
        {"reference": {"productVariantSkus": {"containsAll": []}}},
        {"reference": {"pageSlugs": {"containsAny": []}}},
        {"reference": {"productSlugs": {"containsAny": []}}},
        {"reference": {"productVariantSkus": {"containsAny": []}}},
        {"reference": {"referencedIds": {"containsAny": []}}},
        {"reference": {"pageSlugs": {"containsAny": [], "containsAll": []}}},
        {"reference": {"productSlugs": {"containsAny": [], "containsAll": []}}},
        {"reference": {"productVariantSkus": {"containsAny": [], "containsAll": []}}},
        {"reference": {"referencedIds": {"containsAny": [], "containsAll": []}}},
        {"reference": {"referencedIds": {"containsAll": None}}},
        {"reference": {"pageSlugs": {"containsAll": None}}},
        {"reference": {"productSlugs": {"containsAll": None}}},
        {"reference": {"productVariantSkus": {"containsAll": None}}},
        {"reference": {"pageSlugs": {"containsAny": None}}},
        {"reference": {"productSlugs": {"containsAny": None}}},
        {"reference": {"productVariantSkus": {"containsAny": None}}},
        {"reference": {"referencedIds": {"containsAny": None}}},
    ],
)
def test_pages_query_failed_filter_validation_for_reference_attribute_with_slug_input(
    attribute_value_filter,
    staff_api_client,
    page_type,
    page_type_product_reference_attribute,
):
    # given
    attr_slug_input = "reference-product"

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": attr_slug_input,
                    "value": attribute_value_filter,
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["pages"] is None


@pytest.mark.parametrize(
    "attribute_filter",
    [
        # Non-existing attribute slug
        [{"slug": "non-existing-attribute"}],
        # Existing attribute with non-existing value name
        [{"slug": "tag", "value": {"name": {"eq": "Non-existing Name"}}}],
        [{"value": {"name": {"eq": "Non-existing Name"}}}],
        # Existing numeric attribute with out-of-range value
        [{"slug": "count", "value": {"numeric": {"eq": 999}}}],
        [{"value": {"numeric": {"eq": 999}}}],
        # Existing boolean attribute with no matching boolean value
        [{"slug": "boolean", "value": {"boolean": False}}],
        [{"value": {"boolean": False}}],
        # Multiple attributes where one doesn't exist
        [
            {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
        [
            {"value": {"slug": {"eq": "10"}}},
            {"slug": "non-existing-attr", "value": {"slug": {"eq": "some-value"}}},
        ],
    ],
)
def test_pages_query_with_non_matching_records(
    attribute_filter,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
    tag_page_attribute,
    boolean_attribute,
    numeric_attribute_without_unit,
    date_attribute,
    date_time_attribute,
):
    # given
    boolean_attribute.type = "PAGE_TYPE"
    boolean_attribute.save()
    numeric_attribute_without_unit.type = "PAGE_TYPE"
    numeric_attribute_without_unit.save()

    page_type.page_attributes.add(size_page_attribute)
    page_type.page_attributes.add(tag_page_attribute)
    page_type.page_attributes.add(boolean_attribute)
    page_type.page_attributes.add(numeric_attribute_without_unit)
    page_type.page_attributes.add(date_attribute)
    page_type.page_attributes.add(date_time_attribute)

    size_value = size_page_attribute.values.get(slug="10")
    tag_value = tag_page_attribute.values.get(name="About")
    boolean_value = boolean_attribute.values.filter(boolean=True).first()
    numeric_value = numeric_attribute_without_unit.values.first()
    date_time_value = date_time_attribute.values.first()
    date_value = date_attribute.values.first()

    date_attribute.slug = "date"
    date_attribute.save()
    date_time_attribute.slug = "date_time"
    date_time_attribute.save()

    associate_attribute_values_to_instance(
        page_list[0],
        {
            size_page_attribute.pk: [size_value],
            tag_page_attribute.pk: [tag_value],
            boolean_attribute.pk: [boolean_value],
            numeric_attribute_without_unit.pk: [numeric_value],
            date_attribute.pk: [date_value],
            date_time_attribute.pk: [date_time_value],
        },
    )

    variables = {"where": {"attributes": attribute_filter}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 0


@pytest.mark.parametrize(
    ("attribute_where_input", "expected_count_result"),
    [
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
                {"slug": "author", "value": {"slug": {"oneOf": ["test-author-1"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "15"}}},
                {"slug": "tag", "value": {"name": {"eq": "Help"}}},
                {"slug": "boolean", "value": {"boolean": False}},
            ],
            0,
        ),
        (
            [
                {
                    "slug": "author",
                    "value": {"slug": {"oneOf": ["test-author-1", "test-author-2"]}},
                },
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "author", "value": {"name": {"eq": "Test author 1"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"eq": "10"}}},
                {"slug": "tag", "value": {"name": {"eq": "About"}}},
                {"slug": "author", "value": {"slug": {"eq": "test-author-1"}}},
            ],
            1,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"oneOf": ["10", "15"]}}},
                {"slug": "tag", "value": {"name": {"oneOf": ["About", "Help"]}}},
            ],
            2,
        ),
        (
            [
                {"slug": "page-size", "value": {"slug": {"oneOf": ["10", "15"]}}},
                {"slug": "boolean", "value": {"boolean": True}},
            ],
            1,
        ),
        ([{"value": {"slug": {"oneOf": ["test-author-1", "test-author-2"]}}}], 2),
        (
            [
                {"value": {"slug": {"oneOf": ["10", "15"]}}},
                {"value": {"boolean": True}},
            ],
            1,
        ),
    ],
)
def test_pages_query_with_multiple_attribute_filters(
    attribute_where_input,
    expected_count_result,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
    tag_page_attribute,
    author_page_attribute,
    boolean_attribute,
):
    # given
    boolean_attribute.type = "PAGE_TYPE"
    boolean_attribute.save()

    page_type.page_attributes.add(size_page_attribute)
    page_type.page_attributes.add(tag_page_attribute)
    page_type.page_attributes.add(author_page_attribute)
    page_type.page_attributes.add(boolean_attribute)

    size_value = size_page_attribute.values.get(slug="10")
    tag_value = tag_page_attribute.values.get(name="About")
    author_value = author_page_attribute.values.get(slug="test-author-1")
    second_author_value = author_page_attribute.values.get(slug="test-author-2")

    boolean_value = boolean_attribute.values.filter(boolean=True).first()

    associate_attribute_values_to_instance(
        page_list[0],
        {
            size_page_attribute.pk: [size_value],
            tag_page_attribute.pk: [tag_value],
            author_page_attribute.pk: [author_value],
            boolean_attribute.pk: [boolean_value],
        },
    )

    tag_value_2 = tag_page_attribute.values.get(name="Help")
    size_value_15 = size_page_attribute.values.get(slug="15")

    associate_attribute_values_to_instance(
        page_list[1],
        {
            size_page_attribute.pk: [size_value_15],
            tag_page_attribute.pk: [tag_value_2],
            author_page_attribute.pk: [second_author_value],
        },
    )

    variables = {"where": {"attributes": attribute_where_input}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == expected_count_result
