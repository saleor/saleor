import pytest

from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"numeric": None},
        {"name": None},
        {"slug": None},
        {"boolean": False},
        {"reference": {"referencedIds": {"containsAll": ["global-id-1"]}}},
    ],
)
def test_product_variants_query_failed_filter_validation_for_numeric_with_slug_input(
    attribute_value_filter,
    staff_api_client,
    numeric_attribute_without_unit,
    product_variant_list,
    channel_USD,
):
    # given
    attr_slug_input = "numeric"
    numeric_attribute_without_unit.slug = attr_slug_input
    numeric_attribute_without_unit.save()

    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(numeric_attribute_without_unit)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"boolean": None},
        {"name": None},
        {"slug": None},
        {"numeric": {"eq": 1.2}},
        {"reference": {"referencedIds": {"containsAll": ["global-id-1"]}}},
    ],
)
def test_product_variants_query_failed_filter_validation_for_boolean_with_slug_input(
    attribute_value_filter,
    staff_api_client,
    boolean_attribute,
    product_variant_list,
    channel_USD,
):
    # given
    attr_slug_input = "boolean"
    boolean_attribute.slug = attr_slug_input
    boolean_attribute.save()

    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(boolean_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


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
def test_product_variants_query_failed_filter_validation_for_date_attribute_with_slug_input(
    attribute_value_filter,
    staff_api_client,
    date_attribute,
    product_variant_list,
    channel_USD,
):
    # given
    attr_slug_input = "date"
    date_attribute.slug = attr_slug_input
    date_attribute.save()

    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(date_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


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
def test_product_variants_query_failed_filter_validation_for_datetime_attribute_with_slug_input(
    attribute_value_filter,
    staff_api_client,
    date_time_attribute,
    product_variant_list,
    channel_USD,
):
    # given
    attr_slug_input = "date_time"
    date_time_attribute.slug = attr_slug_input
    date_time_attribute.save()

    product_type = product_variant_list[0].product.product_type
    product_type.variant_attributes.add(date_time_attribute)

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


@pytest.mark.parametrize(
    "attribute_value_filter",
    [
        {"slug": None, "value": None},
        {"slug": None, "value": {"name": {"eq": "name"}}},
    ],
)
def test_product_variants_query_failed_filter_validation_null_in_input(
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


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
def test_product_variants_query_failed_filter_validation_for_basic_value_fields_with_attr_slug(
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


def test_product_variants_query_failed_filter_validation_for_duplicated_attr_slug(
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
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None


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
def test_product_variants_query_failed_filter_validation_for_reference_attribute_with_slug_input(
    attribute_value_filter,
    staff_api_client,
    channel_USD,
):
    # given
    attr_slug_input = "reference-product"

    variables = {
        "where": {
            "attributes": [{"slug": attr_slug_input, "value": attribute_value_filter}]
        },
        "channel": channel_USD.slug,
    }
    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert "errors" in content
    assert content["data"]["productVariants"] is None
