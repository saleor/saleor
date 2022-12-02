from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ....product.models import Product, ProductVariant
from ...tests.utils import get_graphql_content

QUERY_VARIANTS_FILTER = """
query variants($filter: ProductVariantFilterInput){
    productVariants(first:10, filter: $filter){
        edges{
            node{
                name
                sku
            }
        }
    }
}
"""


@pytest.fixture
def products_for_variant_filtering(product_type, category):
    products = Product.objects.bulk_create(
        [
            Product(
                name="Product1",
                slug="prod1",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="ProductProduct1",
                slug="prod_prod1",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="ProductProduct2",
                slug="prod_prod2",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="Product2",
                slug="prod2",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="Product3",
                slug="prod3",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="ProductNoSku",
                slug="prod4",
                category=category,
                product_type=product_type,
            ),
            Product(
                name="ProductWithPreorder",
                slug="prod5",
                category=category,
                product_type=product_type,
            ),
        ]
    )
    ProductVariant.objects.bulk_create(
        [
            ProductVariant(
                product=products[0],
                sku="P1-V1",
            ),
            ProductVariant(
                product=products[0],
                sku="P1-V2",
            ),
            ProductVariant(product=products[1], sku="PP1-V1", name="XL"),
            ProductVariant(product=products[2], sku="PP2-V1", name="XXL"),
            ProductVariant(
                product=products[3],
                sku="P2-V1",
            ),
            ProductVariant(
                product=products[4],
                sku="P3-V1",
            ),
            ProductVariant(
                product=products[5],
                sku="P-NO-SKU",
            ),
            ProductVariant(
                product=products[5],
            ),
            ProductVariant(
                product=products[6],
                sku="Preorder-V1",
                is_preorder=True,
            ),
            ProductVariant(
                product=products[6],
                sku="Preorder-V2",
                is_preorder=True,
                preorder_end_date=timezone.now() + timedelta(days=1),
            ),
            ProductVariant(
                product=products[6],
                sku="Preorder-V3",
                is_preorder=True,
                preorder_end_date=timezone.now() - timedelta(days=1),
            ),
        ]
    )
    return products


@pytest.mark.parametrize(
    "filter_by, variants",
    [
        ({"search": "Product1"}, ["P1-V1", "P1-V2", "PP1-V1"]),
        ({"search": "Product3"}, ["P3-V1"]),
        ({"search": "XL"}, ["PP1-V1", "PP2-V1"]),
        ({"search": "XXL"}, ["PP2-V1"]),
        ({"search": "PP2-V1"}, ["PP2-V1"]),
        ({"search": "P1"}, ["P1-V1", "P1-V2", "PP1-V1"]),
        ({"search": "invalid"}, []),
        ({"search": "ProductNoSku"}, ["P-NO-SKU", None]),
        ({"sku": ["P1"]}, []),
        ({"sku": ["P1-V1", "P1-V2", "PP1-V1"]}, ["P1-V1", "P1-V2", "PP1-V1"]),
        ({"sku": ["PP1-V1", "PP2-V1"]}, ["PP1-V1", "PP2-V1"]),
        ({"sku": ["invalid"]}, []),
        ({"isPreorder": True}, ["Preorder-V1", "Preorder-V2"]),
        (
            {"isPreorder": False},
            [
                "P-NO-SKU",
                "P1-V1",
                "P1-V2",
                "P2-V1",
                "P3-V1",
                "PP1-V1",
                "PP2-V1",
                "Preorder-V3",
                None,
            ],
        ),
    ],
)
def test_products_pagination_with_filtering(
    filter_by,
    variants,
    staff_api_client,
    permission_manage_products,
    products_for_variant_filtering,
):
    # given
    variables = {"filter": filter_by}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VARIANTS_FILTER,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["productVariants"]["edges"]
    assert sorted([variant for variant in variants if variant is not None]) == sorted(
        [
            product_node["node"]["sku"]
            for product_node in products_nodes
            if product_node["node"]["sku"] is not None
        ]
    )
    if None in variants:
        assert variants.count(None) == len(
            [
                product_node["node"]["sku"]
                for product_node in products_nodes
                if product_node["node"]["sku"] is None
            ]
        )


@pytest.mark.parametrize(
    "variants_filter, count",
    [
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 2),
        ({"updatedAt": {"lte": "2012-01-14T12:00:05+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T11:59:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2012-01-14T11:05:00+00:00"}}, 1),
        ({"updatedAt": {"gte": "2012-01-14T12:01:00+00:00"}}, 0),
        ({"updatedAt": {"lte": "2012-01-14T10:59:00+00:00"}}, 0),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:01:00+00:00",
                    "gte": "2012-01-14T11:59:00+00:00",
                },
            },
            1,
        ),
    ],
)
def test_product_variant_query_with_filter_updated_at(
    variants_filter,
    count,
    product_type,
    category,
    staff_api_client,
    permission_manage_products,
):
    product = Product.objects.create(
        name="Product1",
        slug="prod1",
        category=category,
        product_type=product_type,
    )

    with freeze_time("2012-01-14 11:00:00"):
        ProductVariant.objects.create(product=product, sku="P1-V1")

    with freeze_time("2012-01-14 12:00:00"):
        ProductVariant.objects.create(product=product, sku="P1-V2")

    variables = {"filter": variants_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    response = staff_api_client.post_graphql(QUERY_VARIANTS_FILTER, variables)
    content = get_graphql_content(response)
    variants = content["data"]["productVariants"]["edges"]

    assert len(variants) == count
