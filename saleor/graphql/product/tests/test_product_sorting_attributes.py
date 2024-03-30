import os.path
from decimal import Decimal

import graphene
import pytest

from ....attribute import AttributeInputType, AttributeType
from ....attribute import models as attribute_models
from ....attribute.utils import associate_attribute_values_to_instance
from ....product import ProductTypeKind
from ....product import models as product_models
from ...tests.utils import get_graphql_content

HERE = os.path.realpath(os.path.dirname(__file__))

QUERY_SORT_PRODUCTS_BY_ATTRIBUTE = """
query products(
  $field: ProductOrderField
  $attributeId: ID
  $direction: OrderDirection!
  $channel: String
) {
  products(
    first: 100,
    channel: $channel,
    sortBy: { field: $field, attributeId: $attributeId, direction: $direction }
  ) {
    edges {
      node {
        name
        attributes {
          attribute {
            slug
          }
          values {
            name
          }
        }
      }
    }
  }
}
"""

COLORS = (["Blue", "Red"], ["Blue", "Gray"], ["Pink"], ["Pink"], ["Green"])
TRADEMARKS = ("A", "A", "ab", "b", "y")
DUMMIES = ("Oopsie",)


@pytest.fixture
def products_structures(category, channel_USD):
    def attr_value(attribute, *values):
        return [attribute.values.get_or_create(name=v, slug=v)[0] for v in values]

    assert product_models.Product.objects.count() == 0

    in_multivals = AttributeInputType.MULTISELECT

    pt_apples, pt_oranges, pt_other = list(
        product_models.ProductType.objects.bulk_create(
            [
                product_models.ProductType(
                    name="Apples", slug="apples", has_variants=False
                ),
                product_models.ProductType(
                    name="Oranges", slug="oranges", has_variants=False
                ),
                product_models.ProductType(
                    name="Other attributes", slug="other", has_variants=False
                ),
            ]
        )
    )

    colors_attr, trademark_attr, dummy_attr = list(
        attribute_models.Attribute.objects.bulk_create(
            [
                attribute_models.Attribute(
                    name="Colors",
                    slug="colors",
                    input_type=in_multivals,
                    type=AttributeType.PRODUCT_TYPE,
                ),
                attribute_models.Attribute(
                    name="Trademark", slug="trademark", type=AttributeType.PRODUCT_TYPE
                ),
                attribute_models.Attribute(
                    name="Dummy", slug="dummy", type=AttributeType.PRODUCT_TYPE
                ),
            ]
        )
    )

    # Manually add every attribute to given product types
    # to force the preservation of ordering
    pt_apples.product_attributes.add(colors_attr)
    pt_apples.product_attributes.add(trademark_attr)

    pt_oranges.product_attributes.add(colors_attr)
    pt_oranges.product_attributes.add(trademark_attr)

    pt_other.product_attributes.add(dummy_attr)

    assert len(COLORS) == len(TRADEMARKS)

    apples = list(
        product_models.Product.objects.bulk_create(
            [
                product_models.Product(
                    name=f"{attrs[0]} Apple - {attrs[1]} ({i})",
                    slug=f"{attrs[0]}-apple-{attrs[1]}-({i})",
                    product_type=pt_apples,
                    category=category,
                )
                for i, attrs in enumerate(zip(COLORS, TRADEMARKS))
            ]
        )
    )
    for product_apple in apples:
        product_models.ProductChannelListing.objects.create(
            product=product_apple,
            channel=channel_USD,
            is_published=True,
            visible_in_listings=True,
        )
        variant = product_models.ProductVariant.objects.create(
            product=product_apple, sku=product_apple.slug
        )
        product_models.ProductVariantChannelListing.objects.create(
            variant=variant,
            channel=channel_USD,
            price_amount=Decimal(10),
            cost_price_amount=Decimal(1),
            currency=channel_USD.currency_code,
        )
    oranges = list(
        product_models.Product.objects.bulk_create(
            [
                product_models.Product(
                    name=f"{attrs[0]} Orange - {attrs[1]} ({i})",
                    slug=f"{attrs[0]}-orange-{attrs[1]}-({i})",
                    product_type=pt_oranges,
                    category=category,
                )
                for i, attrs in enumerate(zip(COLORS, TRADEMARKS))
            ]
        )
    )
    for product_orange in oranges:
        product_models.ProductChannelListing.objects.create(
            product=product_orange,
            channel=channel_USD,
            is_published=True,
            visible_in_listings=True,
        )
        variant = product_models.ProductVariant.objects.create(
            product=product_orange, sku=product_orange.slug
        )
        product_models.ProductVariantChannelListing.objects.create(
            variant=variant,
            channel=channel_USD,
            cost_price_amount=Decimal(1),
            price_amount=Decimal(10),
            currency=channel_USD.currency_code,
        )
    dummy = product_models.Product.objects.create(
        name="Oopsie Dummy",
        slug="oopsie-dummy",
        product_type=pt_other,
        category=category,
    )
    product_models.ProductChannelListing.objects.create(
        product=dummy,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = product_models.ProductVariant.objects.create(
        product=dummy, sku=dummy.slug
    )
    product_models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    other_dummy = product_models.Product.objects.create(
        name="Another Dummy but first in ASC and has no attribute value",
        slug="another-dummy",
        product_type=pt_other,
        category=category,
    )
    product_models.ProductChannelListing.objects.create(
        product=other_dummy,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )
    variant = product_models.ProductVariant.objects.create(
        product=other_dummy, sku=other_dummy.slug
    )
    product_models.ProductVariantChannelListing.objects.create(
        variant=variant,
        channel=channel_USD,
        cost_price_amount=Decimal(1),
        price_amount=Decimal(10),
        currency=channel_USD.currency_code,
    )
    dummy_attr_value = attr_value(dummy_attr, DUMMIES[0])
    associate_attribute_values_to_instance(
        dummy,
        {dummy_attr.pk: dummy_attr_value},
    )

    for products in (apples, oranges):
        for product, attr_values in zip(products, COLORS):
            attr_values = attr_value(colors_attr, *attr_values)
            associate_attribute_values_to_instance(
                product,
                {colors_attr.pk: attr_values},
            )

        for product, attr_values in zip(products, TRADEMARKS):
            attr_values = attr_value(trademark_attr, attr_values)
            associate_attribute_values_to_instance(
                product,
                {trademark_attr.pk: attr_values},
            )

    return colors_attr, trademark_attr, dummy_attr


def test_sort_products_cannot_sort_both_by_field_and_by_attribute(
    api_client, channel_USD
):
    """Test that sorting by field and by attribute are mutually exclusive."""
    query = QUERY_SORT_PRODUCTS_BY_ATTRIBUTE
    variables = {
        "field": "NAME",
        "attributeId": "SomeAttributeId",
        "direction": "ASC",
        "channel": channel_USD.slug,
    }

    response = api_client.post_graphql(query, variables)
    response = get_graphql_content(response, ignore_errors=True)

    errors = response.get("errors", [])

    assert len(errors) == 1, response
    assert errors[0]["message"] == (
        "You must provide either `field` or `attributeId` to sort the products."
    )


# Ordered by the given attribute value, then by the product name.
#
# If the product doesn't have a value, it will be placed at the bottom of the products
# having a value and will be ordered by their product name.
#
# If the product doesn't have such attribute in its product type, it will be placed
# at the end of the other products having such attribute. They will be ordered by their
# name as well.
EXPECTED_SORTED_DATA_SINGLE_VALUE_ASC = [
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Gray"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Gray'] Apple - A (1)",
        }
    },
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Gray"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Gray'] Orange - A (1)",
        }
    },
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Red"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Red'] Apple - A (0)",
        }
    },
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Red"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Red'] Orange - A (0)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "ab"}]},
            ],
            "name": "['Pink'] Apple - ab (2)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "ab"}]},
            ],
            "name": "['Pink'] Orange - ab (2)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "b"}]},
            ],
            "name": "['Pink'] Apple - b (3)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "b"}]},
            ],
            "name": "['Pink'] Orange - b (3)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Green"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "y"}]},
            ],
            "name": "['Green'] Apple - y (4)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Green"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "y"}]},
            ],
            "name": "['Green'] Orange - y (4)",
        }
    },
    {
        "node": {
            "attributes": [{"attribute": {"slug": "dummy"}, "values": []}],
            "name": "Another Dummy but first in ASC and has no attribute value",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "dummy"}, "values": [{"name": "Oopsie"}]}
            ],
            "name": "Oopsie Dummy",
        }
    },
]

EXPECTED_SORTED_DATA_MULTIPLE_VALUES_ASC = [
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Gray"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Gray'] Apple - A (1)",
        }
    },
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Gray"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Gray'] Orange - A (1)",
        }
    },
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Red"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Red'] Apple - A (0)",
        }
    },
    {
        "node": {
            "attributes": [
                {
                    "attribute": {"slug": "colors"},
                    "values": [{"name": "Blue"}, {"name": "Red"}],
                },
                {"attribute": {"slug": "trademark"}, "values": [{"name": "A"}]},
            ],
            "name": "['Blue', 'Red'] Orange - A (0)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Green"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "y"}]},
            ],
            "name": "['Green'] Apple - y (4)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Green"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "y"}]},
            ],
            "name": "['Green'] Orange - y (4)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "ab"}]},
            ],
            "name": "['Pink'] Apple - ab (2)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "b"}]},
            ],
            "name": "['Pink'] Apple - b (3)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "ab"}]},
            ],
            "name": "['Pink'] Orange - ab (2)",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "colors"}, "values": [{"name": "Pink"}]},
                {"attribute": {"slug": "trademark"}, "values": [{"name": "b"}]},
            ],
            "name": "['Pink'] Orange - b (3)",
        }
    },
    {
        "node": {
            "attributes": [{"attribute": {"slug": "dummy"}, "values": []}],
            "name": "Another Dummy but first in ASC and has no attribute value",
        }
    },
    {
        "node": {
            "attributes": [
                {"attribute": {"slug": "dummy"}, "values": [{"name": "Oopsie"}]}
            ],
            "name": "Oopsie Dummy",
        }
    },
]


@pytest.mark.parametrize("ascending", [True, False])
def test_sort_product_by_attribute_single_value(
    api_client, products_structures, ascending, channel_USD
):
    _, attribute, _ = products_structures
    attribute_id: str = graphene.Node.to_global_id("Attribute", attribute.pk)
    direction = "ASC" if ascending else "DESC"

    query = QUERY_SORT_PRODUCTS_BY_ATTRIBUTE
    variables = {
        "attributeId": attribute_id,
        "direction": direction,
        "channel": channel_USD.slug,
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    products = response["data"]["products"]["edges"]

    assert len(products) == product_models.Product.objects.count()

    if ascending:
        assert products == EXPECTED_SORTED_DATA_SINGLE_VALUE_ASC
    else:
        assert products == list(reversed(EXPECTED_SORTED_DATA_SINGLE_VALUE_ASC))


@pytest.mark.parametrize("ascending", [True, False])
def test_sort_product_by_attribute_multiple_values(
    api_client, products_structures, ascending, channel_USD
):
    attribute, _, _ = products_structures
    attribute_id: str = graphene.Node.to_global_id("Attribute", attribute.pk)
    direction = "ASC" if ascending else "DESC"

    query = QUERY_SORT_PRODUCTS_BY_ATTRIBUTE
    variables = {
        "attributeId": attribute_id,
        "direction": direction,
        "channel": channel_USD.slug,
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    products = response["data"]["products"]["edges"]

    assert len(products) == product_models.Product.objects.count()

    if ascending:
        assert products == EXPECTED_SORTED_DATA_MULTIPLE_VALUES_ASC
    else:
        assert products == list(reversed(EXPECTED_SORTED_DATA_MULTIPLE_VALUES_ASC))


def test_sort_product_not_having_attribute_data(api_client, category, count_queries):
    """Test sorting when an attribute exists but does not have a value.

    For example, when the product's product type was updated after the product
    was created.
    """
    expected_results = ["Z", "Y", "A"]
    product_create_kwargs = {"category": category}

    # Create two product types, with one forced to be at the bottom (no such attribute)
    product_type = product_models.ProductType.objects.create(
        name="Apples", slug="apples"
    )
    other_product_type = product_models.ProductType.objects.create(
        name="Chocolates", slug="chocolates", kind=ProductTypeKind.NORMAL
    )

    # Assign an attribute to the product type
    attribute = attribute_models.Attribute.objects.create(
        name="Kind", slug="kind", type=AttributeType.PRODUCT_TYPE
    )
    value = attribute_models.AttributeValue.objects.create(
        name="Value", slug="value", attribute=attribute
    )
    product_type.product_attributes.add(attribute)

    # Create a product with a value
    product_having_attr_value = product_models.Product.objects.create(
        name="Z", slug="z", product_type=product_type, **product_create_kwargs
    )
    associate_attribute_values_to_instance(
        product_having_attr_value,
        {attribute.pk: [value]},
    )

    # Create a product having the same product type but no attribute data
    product_models.Product.objects.create(
        name="Y", slug="y", product_type=product_type, **product_create_kwargs
    )

    # Create a new product having a name that would be ordered first in ascending
    # as the default ordering is by name for non matching products
    product_models.Product.objects.create(
        name="A", slug="a", product_type=other_product_type, **product_create_kwargs
    )

    # Sort the products
    qs = product_models.Product.objects.sort_by_attribute(attribute_pk=attribute.pk)
    qs = qs.values_list("name", flat=True)

    # Compare the results
    sorted_results = list(qs)
    assert sorted_results == expected_results


@pytest.mark.parametrize(
    "attribute_id",
    [
        "",
        graphene.Node.to_global_id("Attribute", -1),
    ],
)
def test_sort_product_by_attribute_using_invalid_attribute_id(
    api_client, product_list_published, attribute_id, channel_USD
):
    """Ensure passing an empty attribute ID as sorting field does nothing."""

    query = QUERY_SORT_PRODUCTS_BY_ATTRIBUTE

    # Products are ordered in descending order to ensure we
    # are not actually trying to sort them at all
    variables = {
        "attributeId": attribute_id,
        "direction": "DESC",
        "channel": channel_USD.slug,
    }

    response = get_graphql_content(
        api_client.post_graphql(
            query,
            variables,
        ),
        ignore_errors=True,
    )
    products = response["data"]["products"]["edges"]

    assert len(products) == product_models.Product.objects.count()
    assert products[0]["node"]["name"] == product_models.Product.objects.first().name


def test_sort_product_by_attribute_using_string_as_attribute_id(
    api_client, product_list_published, channel_USD
):
    """Ensure passing an invalid attribute ID as sorting field return error."""

    query = QUERY_SORT_PRODUCTS_BY_ATTRIBUTE
    variables = {
        "attributeId": graphene.Node.to_global_id("Attribute", "not a number"),
        "direction": "DESC",
        "channel": channel_USD.slug,
    }

    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    errors = content["errors"][0]

    assert errors["extensions"]["exception"]["code"] == "GraphQLError"


@pytest.mark.parametrize("direction", ["ASC", "DESC"])
def test_sort_product_by_attribute_using_attribute_having_no_products(
    api_client, product_list_published, direction, channel_USD
):
    """Ensure passing an empty attribute ID as sorting field does nothing."""

    query = QUERY_SORT_PRODUCTS_BY_ATTRIBUTE
    attribute_without_products = attribute_models.Attribute.objects.create(
        name="Colors 2", slug="colors-2", type=AttributeType.PRODUCT_TYPE
    )

    attribute_id: str = graphene.Node.to_global_id(
        "Attribute", attribute_without_products.pk
    )
    variables = {
        "attributeId": attribute_id,
        "direction": direction,
        "channel": channel_USD.slug,
    }

    response = get_graphql_content(api_client.post_graphql(query, variables))
    products = response["data"]["products"]["edges"]

    if direction == "ASC":
        expected_first_product = product_models.Product.objects.order_by("slug").first()
    else:
        expected_first_product = product_models.Product.objects.order_by("slug").last()

    assert len(products) == product_models.Product.objects.count()
    assert products[0]["node"]["name"] == expected_first_product.name
