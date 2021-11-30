import warnings

import graphene
from django.db.models import Q

from .....attribute.models import Attribute
from .....channel.models import Channel
from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from .....product import ProductTypeKind
from .....product.models import Category, Product, ProductType
from ....tests.utils import get_graphql_content

QUERY_ATTRIBUTES_WITH_FILTER = """
    query ($filter: AttributeFilterInput!) {
        attributes(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                    slug
                }
            }
        }
    }
"""


def test_attributes_query_with_filter(
    user_api_client,
    product_type,
    category,
    published_collection,
    collection_with_products,
    channel_USD,
):
    Channel.objects.exclude(pk=channel_USD.pk).delete()
    category_id = graphene.Node.to_global_id("Category", category.pk)

    # Create another product type and attribute that shouldn't get matched
    other_category = Category.objects.create(name="Other Category", slug="other-cat")
    other_attribute = Attribute.objects.create(name="Other", slug="other")
    other_product_type = ProductType.objects.create(
        name="Other type",
        has_variants=True,
        is_shipping_required=True,
        kind=ProductTypeKind.NORMAL,
    )
    other_product_type.product_attributes.add(other_attribute)

    # other product
    Product.objects.create(
        name="Another Product", product_type=other_product_type, category=other_category
    )

    expected_qs = Attribute.objects.filter(
        Q(attributeproduct__product_type_id=product_type.pk)
        | Q(attributevariant__product_type_id=product_type.pk)
    )

    variables = {"filter": {"inCategory": category_id}}
    with warnings.catch_warnings(record=True) as warns:
        content = get_graphql_content(
            user_api_client.post_graphql(QUERY_ATTRIBUTES_WITH_FILTER, variables)
        )
    attributes_data = content["data"]["attributes"]["edges"]

    flat_attributes_data = [attr["node"]["slug"] for attr in attributes_data]
    expected_flat_attributes_data = list(expected_qs.values_list("slug", flat=True))

    assert flat_attributes_data == expected_flat_attributes_data
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )
