import pytest

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
        ({"search": ["invalid"]}, []),
        ({"sku": ["P1"]}, []),
        ({"sku": ["P1-V1", "P1-V2", "PP1-V1"]}, ["P1-V1", "P1-V2", "PP1-V1"]),
        ({"sku": ["PP1-V1", "PP2-V1"]}, ["PP1-V1", "PP2-V1"]),
        ({"sku": ["invalid"]}, []),
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
    for index, variant_sku in enumerate(variants):
        assert variant_sku == products_nodes[index]["node"]["sku"]
    assert len(variants) == len(products_nodes)
