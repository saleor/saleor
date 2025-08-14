import pytest

from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_value_filter",
    [{"numeric": None}, {"name": None}, {"slug": None}, {"boolean": False}],
)
def test_products_query_failed_filter_validation_for_numeric_with_slug_input(
    query,
    attribute_value_filter,
    staff_api_client,
    numeric_attribute_without_unit,
    product_type,
    channel_USD,
):
    # given
    attr_slug_input = "numeric"
    numeric_attribute_without_unit.slug = attr_slug_input
    numeric_attribute_without_unit.save()

    product_type.product_attributes.add(numeric_attribute_without_unit)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_value_filter",
    [{"boolean": None}, {"name": None}, {"slug": None}, {"numeric": {"eq": 1.2}}],
)
def test_products_query_failed_filter_validation_for_boolean_with_slug_input(
    query,
    attribute_value_filter,
    staff_api_client,
    boolean_attribute,
    product_type,
    channel_USD,
):
    # given
    attr_slug_input = "boolean"
    boolean_attribute.slug = attr_slug_input
    boolean_attribute.save()

    product_type.product_attributes.add(boolean_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
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
def test_products_query_failed_filter_validation_for_date_attribute_with_slug_input(
    query,
    attribute_value_filter,
    staff_api_client,
    date_attribute,
    product_type,
    channel_USD,
):
    # given
    attr_slug_input = "date"
    date_attribute.slug = attr_slug_input
    date_attribute.save()

    product_type.product_attributes.add(date_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
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
def test_products_query_failed_filter_validation_for_datetime_attribute_with_slug_input(
    query,
    attribute_value_filter,
    staff_api_client,
    date_time_attribute,
    product_type,
    channel_USD,
):
    # given
    attr_slug_input = "date_time"
    date_time_attribute.slug = attr_slug_input
    date_time_attribute.save()

    product_type.product_attributes.add(date_time_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"slug": None, "value": None},
        {"slug": None, "value": {"name": {"eq": "name"}}},
    ],
)
def test_products_query_failed_filter_validation_null_in_input(
    query,
    attribute_value_filter,
    staff_api_client,
    channel_USD,
):
    # given
    variables = {
        "where": {"attributes": [attribute_value_filter]},
        "channel": channel_USD.slug,
    }
    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
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
def test_products_query_failed_filter_validation_for_basic_value_fields_with_attr_slug(
    query,
    attribute_value_filter,
    staff_api_client,
    channel_USD,
):
    # given
    attr_slug_input = "product-size"

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }
    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
def test_products_query_failed_filter_validation_for_duplicated_attr_slug(
    query,
    staff_api_client,
    channel_USD,
):
    # given
    attr_slug_input = "product-size"

    variables = {
        "where": {
            "attributes": [
                {"slug": attr_slug_input},
                {"slug": attr_slug_input},
            ]
        },
        "channel": channel_USD.slug,
    }
    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
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
        {"reference": {"referencedIds": {"containsAny": ["non-existing-id"]}}},
        {"reference": {"referencedIds": {"containsAll": ["non-existing-id"]}}},
        # ID of not valid object
        {"reference": {"referencedIds": {"containsAny": ["T3JkZXI6MQ=="]}}},
        {"reference": {"referencedIds": {"containsAll": ["T3JkZXI6MQ=="]}}},
    ],
)
def test_products_query_failed_filter_validation_for_reference_attribute_with_slug_input(
    query,
    attribute_value_filter,
    staff_api_client,
    product_type,
    product_type_product_reference_attribute,
    channel_USD,
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
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_filter_input",
    [
        {"values": ["test-slug"]},
        {"valuesRange": {"gte": 1}},
        {"dateTime": {"gte": "2023-01-01T00:00:00Z"}},
        {"date": {"gte": "2023-01-01"}},
        {"boolean": True},
    ],
)
def test_products_query_failed_filter_validation_when_missing_attr_slug_for_deprecated_input(
    query,
    attribute_filter_input,
    staff_api_client,
    channel_USD,
):
    # given

    variables = {
        "where": {
            "attributes": [attribute_filter_input],
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_filter_input",
    [
        {"values": ["test-slug"]},
        {"valuesRange": {"gte": 1}},
        {"dateTime": {"gte": "2023-01-01T00:00:00Z"}},
        {"date": {"gte": "2023-01-01"}},
        {"boolean": True},
    ],
)
def test_products_query_failed_filter_validation_when_multiple_inputs_with_deprecated_and_new(
    query,
    attribute_filter_input,
    staff_api_client,
    channel_USD,
):
    # given

    variables = {
        "where": {
            "attributes": [
                {
                    "slug": "attr-slug",
                    "value": {"name": {"eq": "val-name"}},
                },
                {"slug": "attr-slug2", **attribute_filter_input},
            ]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
@pytest.mark.parametrize(
    "attribute_filter_input",
    [
        {"values": ["test-slug"]},
        {"valuesRange": {"gte": 1}},
        {"dateTime": {"gte": "2023-01-01T00:00:00Z"}},
        {"date": {"gte": "2023-01-01"}},
        {"boolean": True},
    ],
)
def test_products_query_failed_filter_validation_when_providing_deprecated_and_new_input(
    query,
    attribute_filter_input,
    staff_api_client,
    channel_USD,
):
    # given
    attribute_filter_input["value"] = {"name": {"eq": "val-name"}}
    variables = {
        "where": {"attributes": [{"slug": "attr-slug", **attribute_filter_input}]},
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["products"] is None
