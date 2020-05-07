import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import ANY, Mock, patch

import graphene
import pytest
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from graphql_relay import to_global_id
from prices import Money

from saleor.core.taxes import TaxType
from saleor.graphql.core.enums import ReportingPeriod
from saleor.graphql.product.bulk_mutations.products import ProductVariantStocksUpdate
from saleor.graphql.product.utils import create_stocks
from saleor.plugins.manager import PluginsManager
from saleor.product import AttributeInputType
from saleor.product.error_codes import ProductErrorCode
from saleor.product.models import (
    Attribute,
    AttributeValue,
    Category,
    Collection,
    Product,
    ProductImage,
    ProductType,
    ProductVariant,
)
from saleor.product.tasks import update_variants_names
from saleor.product.utils.attributes import associate_attribute_values_to_instance
from saleor.warehouse.models import Allocation, Stock, Warehouse
from tests.api.utils import get_graphql_content
from tests.utils import create_image, create_pdf_file_with_image_ext

from .utils import assert_no_permission, get_multipart_request_body


@pytest.fixture
def query_products_with_filter():
    query = """
        query ($filter: ProductFilterInput!, ) {
          products(first:5, filter: $filter) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    return query


@pytest.fixture
def query_collections_with_filter():
    query = """
    query ($filter: CollectionFilterInput!, ) {
          collections(first:5, filter: $filter) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    return query


@pytest.fixture
def query_categories_with_filter():
    query = """
    query ($filter: CategoryFilterInput!, ) {
          categories(first:5, filter: $filter) {
            totalCount
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    return query


QUERY_FETCH_ALL_PRODUCTS = """
    query {
        products(first: 1) {
            totalCount
            edges {
                node {
                    name
                    isPublished
                }
            }
        }
    }
"""


def test_fetch_all_products(user_api_client, product):
    response = user_api_client.post_graphql(QUERY_FETCH_ALL_PRODUCTS)
    content = get_graphql_content(response)
    num_products = Product.objects.count()
    assert content["data"]["products"]["totalCount"] == num_products
    assert len(content["data"]["products"]["edges"]) == num_products


def test_fetch_all_products_app(
    app_api_client, unavailable_product, permission_manage_products,
):
    response = app_api_client.post_graphql(
        QUERY_FETCH_ALL_PRODUCTS,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    product_data = content["data"]["products"]["edges"][0]["node"]
    assert product_data["name"] == unavailable_product.name
    assert product_data["isPublished"] == unavailable_product.is_published


def test_fetch_unavailable_products(user_api_client, product):
    Product.objects.update(is_published=False)
    query = """
    query {
        products(first: 1) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == 0
    assert not content["data"]["products"]["edges"]


def test_product_query(staff_api_client, product, permission_manage_products, stock):
    category = Category.objects.first()
    product = category.products.first()
    query = """
    query {
        category(id: "%(category_id)s") {
            products(first: 20) {
                edges {
                    node {
                        id
                        name
                        url
                        slug
                        thumbnail{
                            url
                            alt
                        }
                        images {
                            url
                        }
                        variants {
                            name
                        }
                        isAvailable
                        pricing {
                            priceRange {
                                start {
                                    gross {
                                        amount
                                        currency
                                        localized
                                    }
                                    net {
                                        amount
                                        currency
                                        localized
                                    }
                                    currency
                                }
                            }
                        }
                        purchaseCost {
                            start {
                                amount
                            }
                            stop {
                                amount
                            }
                        }
                        margin {
                            start
                            stop
                        }
                    }
                }
            }
        }
    }
    """ % {
        "category_id": graphene.Node.to_global_id("Category", category.id)
    }
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["category"] is not None
    product_edges_data = content["data"]["category"]["products"]["edges"]
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]["node"]
    assert product_data["name"] == product.name
    assert product_data["url"] == ""
    assert product_data["slug"] == product.slug
    gross = product_data["pricing"]["priceRange"]["start"]["gross"]
    assert float(gross["amount"]) == float(product.price.amount)
    from saleor.product.utils.costs import get_product_costs_data

    purchase_cost, margin = get_product_costs_data(product)
    assert purchase_cost.start.amount == product_data["purchaseCost"]["start"]["amount"]
    assert purchase_cost.stop.amount == product_data["purchaseCost"]["stop"]["amount"]
    assert product_data["isAvailable"] is product.is_visible
    assert margin[0] == product_data["margin"]["start"]
    assert margin[1] == product_data["margin"]["stop"]


def test_products_query_with_filter_attributes(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):

    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
    )
    attribute = Attribute.objects.create(slug="new_attr", name="Attr")
    attribute.product_types.add(product_type)
    attr_value = AttributeValue.objects.create(
        attribute=attribute, name="First", slug="first"
    )
    second_product = product
    second_product.id = None
    second_product.product_type = product_type
    second_product.slug = "second-product"
    second_product.save()
    associate_attribute_values_to_instance(second_product, attribute, attr_value)

    variables = {
        "filter": {"attributes": [{"slug": attribute.slug, "value": attr_value.slug}]}
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_product_type(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):
    product_type = ProductType.objects.create(
        name="Custom Type",
        slug="custom-type",
        has_variants=True,
        is_shipping_required=True,
    )
    second_product = product
    second_product.id = None
    second_product.product_type = product_type
    second_product.slug = "second-product"
    second_product.save()

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"filter": {"productType": product_type_id}}

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_category(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):
    category = Category.objects.create(name="Custom", slug="custom")
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.category = category
    second_product.save()

    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {"filter": {"categories": [category_id]}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_has_category_false(
    query_products_with_filter, staff_api_client, product, permission_manage_products
):
    second_product = product
    second_product.category = None
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    variables = {"filter": {"hasCategory": False}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_has_category_true(
    query_products_with_filter,
    staff_api_client,
    product_without_category,
    permission_manage_products,
):
    category = Category.objects.create(name="Custom", slug="custom")
    second_product = product_without_category
    second_product.category = category
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    variables = {"filter": {"hasCategory": True}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


def test_products_query_with_filter_collection(
    query_products_with_filter,
    staff_api_client,
    product,
    collection,
    permission_manage_products,
):
    second_product = product
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()
    second_product.collections.add(collection)

    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"filter": {"collections": [collection_id]}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


@pytest.mark.parametrize(
    "products_filter",
    [
        {"price": {"gte": 5.0, "lte": 9.0}},
        {"minimalPrice": {"gte": 1.0, "lte": 2.0}},
        {"isPublished": False},
        {"search": "Juice1"},
    ],
)
def test_products_query_with_filter(
    products_filter,
    query_products_with_filter,
    staff_api_client,
    product,
    permission_manage_products,
):
    assert product.price == Money("10.00", "USD")
    assert product.minimal_variant_price == Money("10.00", "USD")
    assert product.is_published is True
    assert "Juice1" not in product.name

    second_product = product
    second_product.id = None
    second_product.name = "Apple Juice1"
    second_product.slug = "apple-juice1"
    second_product.price = Money("6.00", "USD")
    second_product.minimal_variant_price = Money("1.99", "USD")
    second_product.is_published = products_filter.get("isPublished", True)
    second_product.save()

    variables = {"filter": products_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id("Product", second_product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == second_product_id
    assert products[0]["node"]["name"] == second_product.name


@pytest.mark.parametrize("is_published", [(True), (False)])
def test_products_query_with_filter_search_by_sku(
    is_published,
    query_products_with_filter,
    staff_api_client,
    product_with_two_variants,
    product_with_default_variant,
    permission_manage_products,
):
    product_with_default_variant.is_published = is_published
    product_with_default_variant.save(update_fields=["is_published"])
    variables = {"filter": {"search": "1234"}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product_with_default_variant.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product_with_default_variant.name


def test_products_query_with_filter_stock_availability(
    query_products_with_filter,
    staff_api_client,
    product,
    order_line,
    permission_manage_products,
):
    stock = product.variants.first().stocks.first()
    Allocation.objects.create(
        order_line=order_line, stock=stock, quantity_allocated=stock.quantity
    )
    variables = {"filter": {"stockAvailability": "OUT_OF_STOCK"}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_products_with_filter, variables)
    content = get_graphql_content(response)
    product_id = graphene.Node.to_global_id("Product", product.id)
    products = content["data"]["products"]["edges"]

    assert len(products) == 1
    assert products[0]["node"]["id"] == product_id
    assert products[0]["node"]["name"] == product.name


@pytest.mark.parametrize(
    "quantity_input, warehouse_indexes, count, indexes_of_products_in_result",
    [
        ({"lte": "80", "gte": "20"}, [1, 2], 1, [1]),
        ({"lte": "120", "gte": "40"}, [1, 2], 1, [0]),
        ({"gte": "10"}, [1], 1, [1]),
        ({"gte": "110"}, [2], 0, []),
        (None, [1], 1, [1]),
        (None, [2], 2, [0, 1]),
        ({"lte": "210", "gte": "70"}, [], 1, [0]),
        ({"lte": "90"}, [], 1, [1]),
        ({"lte": "90", "gte": "75"}, [], 0, []),
    ],
)
def test_products_query_with_filter_stocks(
    quantity_input,
    warehouse_indexes,
    count,
    indexes_of_products_in_result,
    query_products_with_filter,
    staff_api_client,
    product_with_single_variant,
    product_with_two_variants,
    warehouse,
):
    product1 = product_with_single_variant
    product2 = product_with_two_variants
    products = [product1, product2]

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    third_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    third_warehouse.slug = "third warehouse"
    third_warehouse.pk = None
    third_warehouse.save()

    warehouses = [warehouse, second_warehouse, third_warehouse]
    warehouse_pks = [
        graphene.Node.to_global_id("Warehouse", warehouses[index].pk)
        for index in warehouse_indexes
    ]

    Stock.objects.bulk_create(
        [
            Stock(
                warehouse=third_warehouse,
                product_variant=product1.variants.first(),
                quantity=100,
            ),
            Stock(
                warehouse=second_warehouse,
                product_variant=product2.variants.first(),
                quantity=10,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=product2.variants.first(),
                quantity=25,
            ),
            Stock(
                warehouse=third_warehouse,
                product_variant=product2.variants.last(),
                quantity=30,
            ),
        ]
    )

    variables = {
        "filter": {
            "stocks": {"quantity": quantity_input, "warehouseIds": warehouse_pks}
        }
    }
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables, check_no_permissions=False
    )
    content = get_graphql_content(response)
    products_data = content["data"]["products"]["edges"]

    product_ids = {
        graphene.Node.to_global_id("Product", products[index].pk)
        for index in indexes_of_products_in_result
    }

    assert len(products_data) == count
    assert {node["node"]["id"] for node in products_data} == product_ids


def test_query_product_image_by_id(user_api_client, product_with_image):
    image = product_with_image.images.first()
    query = """
    query productImageById($imageId: ID!, $productId: ID!) {
        product(id: $productId) {
            imageById(id: $imageId) {
                id
                url
            }
        }
    }
    """
    variables = {
        "productId": graphene.Node.to_global_id("Product", product_with_image.pk),
        "imageId": graphene.Node.to_global_id("ProductImage", image.pk),
    }
    response = user_api_client.post_graphql(query, variables)
    get_graphql_content(response)


def test_product_with_collections(
    staff_api_client, product, collection, permission_manage_products
):
    query = """
        query getProduct($productID: ID!) {
            product(id: $productID) {
                collections {
                    name
                }
            }
        }
        """
    product.collections.add(collection)
    product.save()
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"productID": product_id}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]
    assert data["collections"][0]["name"] == collection.name
    assert len(data["collections"]) == 1


def test_fetch_product_by_id(user_api_client, product):
    query = """
    query ($productId: ID!) {
        product(id: $productId) {
            name
        }
    }
    """
    variables = {"productId": graphene.Node.to_global_id("Product", product.id)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_data = content["data"]["product"]
    assert product_data["name"] == product.name


def _fetch_product(client, product, permissions=None):
    query = """
    query ($productId: ID!) {
        product(id: $productId) {
            name,
            isPublished
        }
    }
    """
    variables = {"productId": graphene.Node.to_global_id("Product", product.id)}
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["product"]


def test_fetch_unpublished_product_staff_user(
    staff_api_client, unavailable_product, permission_manage_products
):
    product_data = _fetch_product(
        staff_api_client, unavailable_product, permissions=[permission_manage_products]
    )
    assert product_data["name"] == unavailable_product.name
    assert product_data["isPublished"] == unavailable_product.is_published


def test_fetch_unpublished_product_customer(user_api_client, unavailable_product):
    product_data = _fetch_product(user_api_client, unavailable_product)
    assert product_data is None


def test_fetch_unpublished_product_anonymous_user(api_client, unavailable_product):
    product_data = _fetch_product(api_client, unavailable_product)
    assert product_data is None


def test_filter_products_by_wrong_attributes(user_api_client, product):
    product_attr = product.product_type.product_attributes.get(slug="color")
    attr_value = (
        product.product_type.variant_attributes.get(slug="size").values.first().id
    )
    query = """
    query {
        products(filter:
                    {attributes: {slug: "%(slug)s", value: "%(value)s"}}, first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """ % {
        "slug": product_attr.slug,
        "value": attr_value,
    }

    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    products = content["data"]["products"]["edges"]

    assert products == []


SORT_PRODUCTS_QUERY = """
    query {
        products(sortBy: %(sort_by_product_order)s, first: 2) {
            edges {
                node {
                    isPublished
                    productType{
                        name
                    }
                    pricing {
                        priceRangeUndiscounted {
                            start {
                                gross {
                                    amount
                                }
                            }
                        }
                        priceRange {
                            start {
                                gross {
                                    amount
                                }
                            }
                        }
                    }
                    updatedAt
                }
            }
        }
    }
"""


def test_sort_products(user_api_client, product):
    # set price and update date of the first product
    product.price = Money("10.00", "USD")
    product.minimal_variant_price = Money("10.00", "USD")
    product.updated_at = datetime.utcnow()
    product.save()

    # Create the second product with higher price and date
    product.pk = None
    product.slug = "second-product"
    product.price = Money("20.00", "USD")
    product.minimal_variant_price = Money("20.00", "USD")
    product.updated_at = datetime.utcnow()
    product.save()

    query = SORT_PRODUCTS_QUERY

    # Test sorting by PRICE, ascending
    asc_price_query = query % {"sort_by_product_order": "{field: PRICE, direction:ASC}"}
    response = user_api_client.post_graphql(asc_price_query)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 < price2

    # Test sorting by PRICE, descending
    desc_price_query = query % {
        "sort_by_product_order": "{field: PRICE, direction:DESC}"
    }
    response = user_api_client.post_graphql(desc_price_query)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    price2 = edges[1]["node"]["pricing"]["priceRangeUndiscounted"]["start"]["gross"][
        "amount"
    ]
    assert price1 > price2

    # Test sorting by MINIMAL_PRICE, ascending
    asc_price_query = query % {
        "sort_by_product_order": "{field: MINIMAL_PRICE, direction:ASC}"
    }
    response = user_api_client.post_graphql(asc_price_query)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 < price2

    # Test sorting by MINIMAL_PRICE, descending
    desc_price_query = query % {
        "sort_by_product_order": "{field: MINIMAL_PRICE, direction:DESC}"
    }
    response = user_api_client.post_graphql(desc_price_query)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    price1 = edges[0]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    price2 = edges[1]["node"]["pricing"]["priceRange"]["start"]["gross"]["amount"]
    assert price1 > price2

    # Test sorting by DATE, ascending
    asc_date_query = query % {"sort_by_product_order": "{field: DATE, direction:ASC}"}
    response = user_api_client.post_graphql(asc_date_query)
    content = get_graphql_content(response)
    date_0 = content["data"]["products"]["edges"][0]["node"]["updatedAt"]
    date_1 = content["data"]["products"]["edges"][1]["node"]["updatedAt"]
    assert parse_datetime(date_0) < parse_datetime(date_1)

    # Test sorting by DATE, descending
    desc_date_query = query % {"sort_by_product_order": "{field: DATE, direction:DESC}"}
    response = user_api_client.post_graphql(desc_date_query)
    content = get_graphql_content(response)
    date_0 = content["data"]["products"]["edges"][0]["node"]["updatedAt"]
    date_1 = content["data"]["products"]["edges"][1]["node"]["updatedAt"]
    assert parse_datetime(date_0) > parse_datetime(date_1)


def test_sort_products_published(staff_api_client, product, permission_manage_products):
    # Create the second not published product
    product.slug = "second-product"
    product.pk = None
    product.is_published = False
    product.save()

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Test sorting by PUBLISHED, ascending
    asc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: PUBLISHED, direction:ASC}"
    }
    response = staff_api_client.post_graphql(asc_published_query)
    content = get_graphql_content(response)
    is_published_0 = content["data"]["products"]["edges"][0]["node"]["isPublished"]
    is_published_1 = content["data"]["products"]["edges"][1]["node"]["isPublished"]
    assert is_published_0 is False
    assert is_published_1 is True

    # Test sorting by PUBLISHED, descending
    desc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: PUBLISHED, direction:DESC}"
    }
    response = staff_api_client.post_graphql(desc_published_query)
    content = get_graphql_content(response)
    is_published_0 = content["data"]["products"]["edges"][0]["node"]["isPublished"]
    is_published_1 = content["data"]["products"]["edges"][1]["node"]["isPublished"]
    assert is_published_0 is True
    assert is_published_1 is False


def test_sort_products_product_type_name(
    user_api_client, product, product_with_default_variant
):
    # Test sorting by TYPE, ascending
    asc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:ASC}"
    }
    response = user_api_client.post_graphql(asc_published_query)
    content = get_graphql_content(response)
    edges = content["data"]["products"]["edges"]
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1

    # Test sorting by PUBLISHED, descending
    desc_published_query = SORT_PRODUCTS_QUERY % {
        "sort_by_product_order": "{field: TYPE, direction:DESC}"
    }
    response = user_api_client.post_graphql(desc_published_query)
    content = get_graphql_content(response)
    product_type_name_0 = edges[0]["node"]["productType"]["name"]
    product_type_name_1 = edges[1]["node"]["productType"]["name"]
    assert product_type_name_0 < product_type_name_1


CREATE_PRODUCT_MUTATION = """
       mutation createProduct(
           $input: ProductCreateInput!
       ) {
                productCreate(
                    input: $input) {
                        product {
                            category {
                                name
                            }
                            descriptionJson
                            isPublished
                            chargeTaxes
                            taxType {
                                taxCode
                                description
                            }
                            name
                            slug
                            basePrice {
                                amount
                            }
                            productType {
                                name
                            }
                            attributes {
                                attribute {
                                    slug
                                }
                                values {
                                    slug
                                }
                            }
                          }
                          productErrors {
                            field
                            code
                            message
                          }
                          errors {
                            message
                            field
                          }
                        }
                      }
"""


def test_create_product(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    description_json,
    permission_manage_products,
    settings,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"
    product_is_published = True
    product_charge_taxes = True
    product_tax_rate = "STANDARD"
    product_price = "22.33"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name="Color")
    color_value_slug = color_attr.values.first().slug
    color_attr_id = graphene.Node.to_global_id("Attribute", color_attr.id)

    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_id = graphene.Node.to_global_id("Attribute", size_attribute.id)
    non_existent_attr_value = "The cake is a lie"

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
            "descriptionJson": description_json,
            "isPublished": product_is_published,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "basePrice": product_price,
            "attributes": [
                {"id": color_attr_id, "values": [color_value_slug]},
                {"id": size_attr_id, "values": [non_existent_attr_value]},
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["descriptionJson"] == description_json
    assert data["product"]["isPublished"] == product_is_published
    assert data["product"]["chargeTaxes"] == product_charge_taxes
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert str(data["product"]["basePrice"]["amount"]) == product_price
    values = (
        data["product"]["attributes"][0]["values"][0]["slug"],
        data["product"]["attributes"][1]["values"][0]["slug"],
    )
    assert slugify(non_existent_attr_value) in values
    assert color_value_slug in values


@pytest.mark.parametrize("input_slug", ["", None])
def test_create_product_no_slug_in_input(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
    input_slug,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_is_published = True
    product_tax_rate = "STANDARD"
    product_price = "22.33"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    # test creating root product
    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": input_slug,
            "isPublished": product_is_published,
            "taxCode": product_tax_rate,
            "basePrice": product_price,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == "test-name"
    assert data["product"]["isPublished"] == product_is_published
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert str(data["product"]["basePrice"]["amount"]) == product_price


def test_create_product_no_category_id(
    staff_api_client,
    product_type,
    category,
    size_attribute,
    description_json,
    permission_manage_products,
    monkeypatch,
):
    query = CREATE_PRODUCT_MUTATION

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    product_name = "test name"
    product_is_published = False
    product_tax_rate = "STANDARD"
    product_price = "22.33"
    input_slug = "test-slug"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    variables = {
        "input": {
            "productType": product_type_id,
            "name": product_name,
            "slug": input_slug,
            "isPublished": product_is_published,
            "taxCode": product_tax_rate,
            "basePrice": product_price,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == input_slug
    assert data["product"]["isPublished"] == product_is_published
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"] is None
    assert str(data["product"]["basePrice"]["amount"]) == product_price


def test_create_product_with_negative_weight(
    staff_api_client,
    product_type,
    category,
    description_json,
    permission_manage_products,
):
    query = CREATE_PRODUCT_MUTATION

    description_json = json.dumps(description_json)

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "weight": -1,
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS = """
    mutation createProduct(
        $productTypeId: ID!,
        $categoryId: ID!
        $name: String!,
        $basePrice: Decimal!,
        $sku: String,
        $trackInventory: Boolean)
    {
        productCreate(
            input: {
                category: $categoryId,
                productType: $productTypeId,
                name: $name,
                basePrice: $basePrice,
                sku: $sku,
                trackInventory: $trackInventory
            })
        {
            product {
                id
                name
                slug
                variants{
                    id
                    sku
                    trackInventory
                    quantity
                }
                category {
                    name
                }
                productType {
                    name
                }
            }
            errors {
                message
                field
            }
        }
    }
    """


def test_create_product_without_variants(
    staff_api_client, product_type_without_variant, category, permission_manage_products
):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "test-name"
    product_price = 10
    sku = "sku"
    track_inventory = True

    variables = {
        "productTypeId": product_type_id,
        "categoryId": category_id,
        "name": product_name,
        "basePrice": product_price,
        "sku": sku,
        "trackInventory": track_inventory,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["productType"]["name"] == product_type.name
    assert data["product"]["category"]["name"] == category.name
    assert data["product"]["variants"][0]["sku"] == sku
    assert data["product"]["variants"][0]["trackInventory"] == track_inventory


def test_create_product_without_variants_sku_validation(
    staff_api_client, product_type_without_variant, category, permission_manage_products
):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_price = 10
    quantity = 1
    track_inventory = True

    variables = {
        "productTypeId": product_type_id,
        "categoryId": category_id,
        "name": product_name,
        "basePrice": product_price,
        "sku": None,
        "quantity": quantity,
        "trackInventory": track_inventory,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"][0]["field"] == "sku"
    assert data["errors"][0]["message"] == "This field cannot be blank."


def test_create_product_without_variants_sku_duplication(
    staff_api_client,
    product_type_without_variant,
    category,
    permission_manage_products,
    product_with_default_variant,
):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_price = 10
    track_inventory = True
    sku = "1234"

    variables = {
        "productTypeId": product_type_id,
        "categoryId": category_id,
        "name": product_name,
        "basePrice": product_price,
        "sku": sku,
        "trackInventory": track_inventory,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    assert data["errors"][0]["field"] == "sku"
    assert data["errors"][0]["message"] == "Product with this SKU already exists."


def test_product_create_without_product_type(
    staff_api_client, category, permission_manage_products
):
    query = """
    mutation createProduct($categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                basePrice: "2.5",
                productType: "",
                category: $categoryId}) {
            product {
                id
            }
            errors {
                message
                field
            }
        }
    }
    """

    category_id = graphene.Node.to_global_id("Category", category.id)
    response = staff_api_client.post_graphql(
        query, {"categoryId": category_id}, permissions=[permission_manage_products]
    )
    errors = get_graphql_content(response)["data"]["productCreate"]["errors"]

    assert errors[0]["field"] == "productType"
    assert errors[0]["message"] == "This field cannot be null."


def test_product_create_without_category_and_true_is_published_value(
    staff_api_client, permission_manage_products, product_type
):
    query = """
    mutation createProduct($productTypeId: ID!) {
        productCreate(input: {
                name: "Product",
                basePrice: "2.5",
                productType: $productTypeId,
                isPublished: true
            }) {
            product {
                id
            }
            errors {
                message
                field
            }
        }
    }
    """

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    response = staff_api_client.post_graphql(
        query,
        {"productTypeId": product_type_id},
        permissions=[permission_manage_products],
    )
    errors = get_graphql_content(response)["data"]["productCreate"]["errors"]

    assert errors[0]["field"] == "isPublished"
    assert errors[0]["message"] == "You must select a category to be able to publish"


def test_product_create_with_collections_webhook(
    staff_api_client,
    permission_manage_products,
    collection,
    product_type,
    category,
    monkeypatch,
):
    query = """
    mutation createProduct($productTypeId: ID!, $collectionId: ID!, $categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                basePrice: "2.5",
                productType: $productTypeId,
                isPublished: true,
                collections: [$collectionId],
                category: $categoryId
            }) {
            product {
                id,
                collections {
                    slug
                },
                category {
                    slug
                }
            }
            errors {
                message
                field
            }
        }
    }

    """

    def assert_product_has_collections(product):
        assert product.collections.count() > 0
        assert product.collections.first() == collection

    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.product_created",
        lambda _, product: assert_product_has_collections(product),
    )

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)

    response = staff_api_client.post_graphql(
        query,
        {
            "productTypeId": product_type_id,
            "categoryId": category_id,
            "collectionId": collection_id,
        },
        permissions=[permission_manage_products],
    )

    get_graphql_content(response)


def test_update_product(
    staff_api_client,
    category,
    non_default_category,
    product,
    other_description_json,
    permission_manage_products,
    monkeypatch,
    color_attribute,
):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $categoryId: ID!,
            $name: String!,
            $slug: String!,
            $descriptionJson: JSONString!,
            $isPublished: Boolean!,
            $chargeTaxes: Boolean!,
            $taxCode: String!,
            $basePrice: Decimal!,
            $attributes: [AttributeValueInput!]) {
                productUpdate(
                    id: $productId,
                    input: {
                        category: $categoryId,
                        name: $name,
                        slug: $slug,
                        descriptionJson: $descriptionJson,
                        isPublished: $isPublished,
                        chargeTaxes: $chargeTaxes,
                        taxCode: $taxCode,
                        basePrice: $basePrice,
                        attributes: $attributes
                    }) {
                        product {
                            category {
                                name
                            }
                            descriptionJson
                            isPublished
                            chargeTaxes
                            taxType {
                                taxCode
                                description
                            }
                            name
                            slug
                            basePrice {
                                amount
                            }
                            productType {
                                name
                            }
                            attributes {
                                attribute {
                                    id
                                    name
                                }
                                values {
                                    name
                                    slug
                                }
                            }
                          }
                          errors {
                            message
                            field
                          }
                        }
                      }
    """

    other_description_json = json.dumps(other_description_json)

    product_id = graphene.Node.to_global_id("Product", product.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_name = "updated name"
    product_slug = "updated-product"
    product_is_published = True
    product_charge_taxes = True
    product_tax_rate = "STANDARD"
    product_price = "33.12"
    assert str(product.price.amount) == "10.00"

    # Mock tax interface with fake response from tax gateway
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(description="", code=product_tax_rate),
    )

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)

    variables = {
        "productId": product_id,
        "categoryId": category_id,
        "name": product_name,
        "slug": product_slug,
        "descriptionJson": other_description_json,
        "isPublished": product_is_published,
        "chargeTaxes": product_charge_taxes,
        "taxCode": product_tax_rate,
        "basePrice": product_price,
        "attributes": [{"id": attribute_id, "values": ["Rainbow"]}],
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []
    assert data["product"]["name"] == product_name
    assert data["product"]["slug"] == product_slug
    assert data["product"]["descriptionJson"] == other_description_json
    assert data["product"]["isPublished"] == product_is_published
    assert data["product"]["chargeTaxes"] == product_charge_taxes
    assert data["product"]["taxType"]["taxCode"] == product_tax_rate
    assert str(data["product"]["basePrice"]["amount"]) == product_price
    assert not data["product"]["category"]["name"] == category.name

    attributes = data["product"]["attributes"]

    assert len(attributes) == 1
    assert len(attributes[0]["values"]) == 1

    assert attributes[0]["attribute"]["id"] == attribute_id
    assert attributes[0]["values"][0]["name"] == "Rainbow"
    assert attributes[0]["values"][0]["slug"] == "rainbow"


UPDATE_PRODUCT_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        productUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            product{
                name
                slug
            }
            productErrors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_product_slug(
    staff_api_client,
    product,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_PRODUCT_SLUG_MUTATION
    old_slug = product.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["productErrors"]
    if not error_message:
        assert not errors
        assert data["product"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_slug_exists(
    staff_api_client, product, permission_manage_products
):
    query = UPDATE_PRODUCT_SLUG_MUTATION
    input_slug = "test-slug"

    second_product = Product.objects.get(pk=product.pk)
    second_product.pk = None
    second_product.slug = input_slug
    second_product.save()

    assert input_slug != product.slug

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["productErrors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_product_slug_and_name(
    staff_api_client,
    product,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            productUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                product{
                    name
                    slug
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = product.name
    old_slug = product.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    product.refresh_from_db()
    data = content["data"]["productUpdate"]
    errors = data["productErrors"]
    if not error_message:
        assert data["product"]["name"] == input_name == product.name
        assert data["product"]["slug"] == input_slug == product.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


UPDATE_PRODUCT_PRICE_MUTATION = """
    mutation($id: ID!, $basePrice: Decimal) {
        productUpdate(
            id: $id
            input: {
                basePrice: $basePrice
            }
        ) {
            product{
                name
                slug
            }
            productErrors {
                field
                message
                code
            }
        }
    }
"""


def test_update_product_invalid_price(
    staff_api_client, product, permission_manage_products,
):

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"basePrice": Decimal("-19"), "id": node_id}
    response = staff_api_client.post_graphql(
        UPDATE_PRODUCT_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    errors = data["productErrors"]
    assert errors[0]["field"] == "basePrice"
    assert errors[0]["code"] == ProductErrorCode.INVALID.name


SET_ATTRIBUTES_TO_PRODUCT_QUERY = """
    mutation updateProduct($productId: ID!, $attributes: [AttributeValueInput!]) {
      productUpdate(id: $productId, input: { attributes: $attributes }) {
        productErrors {
          message
          field
          code
        }
      }
    }
"""


def test_update_product_can_only_assign_multiple_values_to_valid_input_types(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensures you cannot assign multiple values to input types
    that are not multi-select. This also ensures multi-select types
    can be assigned multiple values as intended."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    multi_values_attr = Attribute.objects.create(
        name="multi", slug="multi-vals", input_type=AttributeInputType.MULTISELECT
    )
    multi_values_attr.product_types.add(product.product_type)
    multi_values_attr_id = graphene.Node.to_global_id("Attribute", multi_values_attr.id)

    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": ["red", "blue"]}],
    }
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["productErrors"] == [
        {"field": "attributes", "code": ProductErrorCode.INVALID.name, "message": ANY}
    ]

    # Try to assign multiple values from a valid attribute
    variables["attributes"] = [{"id": multi_values_attr_id, "values": ["a", "b"]}]
    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert not data["productErrors"]


def test_update_product_with_existing_attribute_value(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    expected_attribute_values_count = color_attribute.values.count()
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    color = color_attribute.values.only("name").first()

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": [color.name]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert not data["productErrors"]

    assert (
        color_attribute.values.count() == expected_attribute_values_count
    ), "A new attribute value shouldn't have been created"


def test_update_product_without_supplying_required_product_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    product_type = product.product_type
    color_attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)

    # Create and assign a new attribute requiring a value to be always supplied
    required_attribute = Attribute.objects.create(
        name="Required One", slug="required-one", value_required=True
    )
    product_type.product_attributes.add(required_attribute)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": color_attribute_id, "values": ["Blue"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["productErrors"] == [
        {"field": "attributes", "code": ProductErrorCode.REQUIRED.name, "message": ANY}
    ]


def test_update_product_with_non_existing_attribute(
    staff_api_client, product, permission_manage_products, color_attribute
):
    non_existent_attribute_pk = 0
    invalid_attribute_id = graphene.Node.to_global_id(
        "Attribute", non_existent_attribute_pk
    )

    """Ensure assigning an existing value to a product doesn't create a new
    attribute value."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"id": invalid_attribute_id, "values": ["hello"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["productErrors"] == [
        {"field": "attributes", "code": ProductErrorCode.NOT_FOUND.name, "message": ANY}
    ]


def test_update_product_with_no_attribute_slug_or_id(
    staff_api_client, product, permission_manage_products, color_attribute
):
    """Ensure only supplying values triggers a validation error."""

    staff_api_client.user.user_permissions.add(permission_manage_products)

    # Try to assign multiple values from an attribute that does not support such things
    variables = {
        "productId": graphene.Node.to_global_id("Product", product.pk),
        "attributes": [{"values": ["Oopsie!"]}],
    }

    data = get_graphql_content(
        staff_api_client.post_graphql(SET_ATTRIBUTES_TO_PRODUCT_QUERY, variables)
    )["data"]["productUpdate"]
    assert data["productErrors"] == [
        {"field": "attributes", "code": ProductErrorCode.REQUIRED.name, "message": ANY}
    ]


def test_update_product_without_variants(
    staff_api_client, product_with_default_variant, permission_manage_products
):
    query = """
    mutation updateProduct(
        $productId: ID!,
        $sku: String,
        $trackInventory: Boolean)
    {
        productUpdate(
            id: $productId,
            input: {
                sku: $sku,
                trackInventory: $trackInventory,
            })
        {
            product {
                id
                variants{
                    id
                    sku
                    trackInventory
                }
            }
            errors {
                message
                field
            }
        }
    }
    """

    product = product_with_default_variant
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_sku = "test_sku"
    product_track_inventory = False

    variables = {
        "productId": product_id,
        "sku": product_sku,
        "trackInventory": product_track_inventory,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"] == []
    product = data["product"]["variants"][0]
    assert product["sku"] == product_sku
    assert product["trackInventory"] == product_track_inventory


def test_update_product_without_variants_sku_duplication(
    staff_api_client, product_with_default_variant, permission_manage_products, product
):
    query = """
    mutation updateProduct(
        $productId: ID!,
        $sku: String)
    {
        productUpdate(
            id: $productId,
            input: {
                sku: $sku
            })
        {
            product {
                id
            }
            errors {
                message
                field
            }
        }
    }"""
    product = product_with_default_variant
    product_id = graphene.Node.to_global_id("Product", product.pk)
    product_sku = "123"

    variables = {"productId": product_id, "sku": product_sku}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "sku"
    assert data["errors"][0]["message"] == "Product with this SKU already exists."


def test_update_product_with_negative_weight(
    staff_api_client, product_with_default_variant, permission_manage_products, product
):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $weight: WeightScalar)
        {
            productUpdate(
                id: $productId,
                input: {
                    weight: $weight
                })
            {
                product {
                    id
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """
    product = product_with_default_variant
    product_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {"productId": product_id, "weight": -1}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productUpdate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_update_product_without_category_and_true_is_published_value(
    staff_api_client, permission_manage_products, product
):
    query = """
    mutation updateProduct(
        $productId: ID!,
        $isPublished: Boolean)
    {
        productUpdate(
            id: $productId,
            input: {
                isPublished: $isPublished
            })
        {
            product {
                id
            }
            errors {
                message
                field
            }
        }
    }"""

    product.category = None
    product.save()

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "isPublished": True}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    assert data["errors"]
    assert data["errors"][0]["field"] == "isPublished"
    assert (
        data["errors"][0]["message"]
        == "You must select a category to be able to publish"
    )


UPDATE_PRODUCT = """
    mutation updateProduct(
        $productId: ID!,
        $input: ProductInput!)
    {
        productUpdate(
            id: $productId,
            input: $input)
        {
            product {
                id
                name
                slug
            }
            errors {
                message
                field
            }
        }
    }"""


def test_update_product_name(staff_api_client, permission_manage_products, product):
    query = UPDATE_PRODUCT

    product_slug = product.slug
    new_name = "example-product"
    assert new_name != product.name

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "input": {"name": new_name}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    assert data["product"]["name"] == new_name
    assert data["product"]["slug"] == product_slug


def test_update_product_slug_with_existing_value(
    staff_api_client, permission_manage_products, product
):
    query = UPDATE_PRODUCT
    second_product = Product.objects.get(pk=product.pk)
    second_product.id = None
    second_product.slug = "second-product"
    second_product.save()

    assert product.slug != second_product.slug

    product_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"productId": product_id, "input": {"slug": second_product.slug}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    data = get_graphql_content(response)["data"]["productUpdate"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["message"] == "Product with this Slug already exists."


def test_delete_product(staff_api_client, product, permission_manage_products):
    query = """
        mutation DeleteProduct($id: ID!) {
            productDelete(id: $id) {
                product {
                    name
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]


def test_product_type(user_api_client, product_type):
    query = """
    query {
        productTypes(first: 20) {
            totalCount
            edges {
                node {
                    id
                    name
                    products(first: 1) {
                        edges {
                            node {
                                id
                            }
                        }
                    }
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    no_product_types = ProductType.objects.count()
    assert content["data"]["productTypes"]["totalCount"] == no_product_types
    assert len(content["data"]["productTypes"]["edges"]) == no_product_types


def test_product_type_query(
    user_api_client,
    staff_api_client,
    product_type,
    product,
    permission_manage_products,
    monkeypatch,
):
    monkeypatch.setattr(
        PluginsManager,
        "get_tax_code_from_object_meta",
        lambda self, x: TaxType(code="123", description="Standard Taxes"),
    )
    query = """
            query getProductType($id: ID!) {
                productType(id: $id) {
                    name
                    products(first: 20) {
                        totalCount
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    taxRate
                    taxType {
                        taxCode
                        description
                    }
                }
            }
        """
    no_products = Product.objects.count()
    product.is_published = False
    product.save()
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]
    assert data["productType"]["products"]["totalCount"] == no_products
    assert data["productType"]["taxType"]["taxCode"] == "123"
    assert data["productType"]["taxType"]["description"] == "Standard Taxes"


def test_product_type_create_mutation(
    staff_api_client, product_type, permission_manage_products, monkeypatch, settings
):
    settings.VATLAYER_ACCESS_KEY = "test"
    settings.PLUGINS = ["saleor.plugins.vatlayer.plugin.VatlayerPlugin"]
    manager = PluginsManager(plugins=settings.PLUGINS)
    query = """
    mutation createProductType(
        $name: String!,
        $slug: String!,
        $taxCode: String!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $productAttributes: [ID],
        $variantAttributes: [ID]) {
        productTypeCreate(
            input: {
                name: $name,
                slug: $slug,
                taxCode: $taxCode,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes,
                variantAttributes: $variantAttributes}) {
            productType {
            name
            slug
            taxRate
            isShippingRequired
            hasVariants
            variantAttributes {
                name
                values {
                    name
                }
            }
            productAttributes {
                name
                values {
                    name
                }
            }
            }
        }
    }
    """
    product_type_name = "test type"
    slug = "test-type"
    has_variants = True
    require_shipping = True
    product_attributes = product_type.product_attributes.all()
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]

    variables = {
        "name": product_type_name,
        "slug": slug,
        "hasVariants": has_variants,
        "taxCode": "wine",
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
        "variantAttributes": variant_attributes_ids,
    }
    initial_count = ProductType.objects.count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert ProductType.objects.count() == initial_count + 1
    data = content["data"]["productTypeCreate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping

    pa = product_attributes[0]
    assert data["productAttributes"][0]["name"] == pa.name
    pa_values = data["productAttributes"][0]["values"]
    assert sorted([value["name"] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()]
    )

    va = variant_attributes[0]
    assert data["variantAttributes"][0]["name"] == va.name
    va_values = data["variantAttributes"][0]["values"]
    assert sorted([value["name"] for value in va_values]) == sorted(
        [value.name for value in va.values.all()]
    )

    new_instance = ProductType.objects.latest("pk")
    tax_code = manager.get_tax_code_from_object_meta(new_instance).code
    assert tax_code == "wine"


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-product-type"),
        ("", "test-product-type"),
    ),
)
def test_create_product_type_with_given_slug(
    staff_api_client, permission_manage_products, input_slug, expected_slug
):
    query = """
        mutation(
                $name: String, $slug: String) {
            productTypeCreate(
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                productType {
                    id
                    name
                    slug
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """
    name = "Test product type"
    variables = {"name": name, "slug": input_slug}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    assert not data["productErrors"]
    assert data["productType"]["slug"] == expected_slug


def test_create_product_type_create_with_negative_weight(
    staff_api_client, permission_manage_products
):
    query = """
        mutation(
                $name: String, $weight: WeightScalar) {
            productTypeCreate(
                input: {
                    name: $name
                    weight: $weight
                }
            ) {
                productType {
                    id
                    name
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """
    name = "Test product type"
    variables = {"name": name, "weight": -1.1}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeCreate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_product_type_update_mutation(
    staff_api_client, product_type, permission_manage_products
):
    query = """
    mutation updateProductType(
        $id: ID!,
        $name: String!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $productAttributes: [ID],
        ) {
            productTypeUpdate(
            id: $id,
            input: {
                name: $name,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes
            }) {
                productType {
                    name
                    slug
                    isShippingRequired
                    hasVariants
                    variantAttributes {
                        id
                    }
                    productAttributes {
                        id
                    }
                }
              }
            }
    """
    product_type_name = "test type updated"
    slug = product_type.slug
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    # Test scenario: remove all product attributes using [] as input
    # but do not change variant attributes
    product_attributes = []
    product_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in product_attributes
    ]
    variant_attributes = product_type.variant_attributes.all()

    variables = {
        "id": product_type_id,
        "name": product_type_name,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "productAttributes": product_attributes_ids,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]["productType"]
    assert data["name"] == product_type_name
    assert data["slug"] == slug
    assert data["hasVariants"] == has_variants
    assert data["isShippingRequired"] == require_shipping
    assert not data["productAttributes"]
    assert len(data["variantAttributes"]) == (variant_attributes.count())


UPDATE_PRODUCT_TYPE_SLUG_MUTATION = """
    mutation($id: ID!, $slug: String) {
        productTypeUpdate(
            id: $id
            input: {
                slug: $slug
            }
        ) {
            productType{
                name
                slug
            }
            productErrors {
                field
                message
                code
            }
        }
    }
"""


@pytest.mark.parametrize(
    "input_slug, expected_slug, error_message",
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_product_type_slug(
    staff_api_client,
    product_type,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    query = UPDATE_PRODUCT_TYPE_SLUG_MUTATION
    old_slug = product_type.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["productErrors"]
    if not error_message:
        assert not errors
        assert data["productType"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_type_slug_exists(
    staff_api_client, product_type, permission_manage_products
):
    query = UPDATE_PRODUCT_TYPE_SLUG_MUTATION
    input_slug = "test-slug"

    second_product_type = ProductType.objects.get(pk=product_type.pk)
    second_product_type.pk = None
    second_product_type.slug = input_slug
    second_product_type.save()

    assert input_slug != product_type.slug

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeUpdate"]
    errors = data["productErrors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == ProductErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    "input_slug, expected_slug, input_name, error_message, error_field",
    [
        ("test-slug", "test-slug", "New name", None, None),
        ("", "", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", "This field cannot be blank.", "name"),
        (None, None, None, "Slug value cannot be blank.", "slug"),
    ],
)
def test_update_product_type_slug_and_name(
    staff_api_client,
    product_type,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    error_message,
    error_field,
):
    query = """
            mutation($id: ID!, $name: String, $slug: String) {
            productTypeUpdate(
                id: $id
                input: {
                    name: $name
                    slug: $slug
                }
            ) {
                productType{
                    name
                    slug
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """

    old_name = product_type.name
    old_slug = product_type.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"slug": input_slug, "name": input_name, "id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    product_type.refresh_from_db()
    data = content["data"]["productTypeUpdate"]
    errors = data["productErrors"]
    if not error_message:
        assert data["productType"]["name"] == input_name == product_type.name
        assert data["productType"]["slug"] == input_slug == product_type.slug
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_update_product_type_with_negative_weight(
    staff_api_client, product_type, permission_manage_products,
):
    query = """
        mutation($id: ID!, $weight: WeightScalar) {
            productTypeUpdate(
                id: $id
                input: {
                    weight: $weight
                }
            ) {
                productType{
                    name
                }
                productErrors {
                    field
                    message
                    code
                }
            }
        }
    """

    node_id = graphene.Node.to_global_id("ProductType", product_type.id)
    variables = {"id": node_id, "weight": "-1"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    product_type.refresh_from_db()
    data = content["data"]["productTypeUpdate"]
    error = data["productErrors"][0]
    assert error["field"] == "weight"
    assert error["code"] == ProductErrorCode.INVALID.name


def test_product_type_delete_mutation(
    staff_api_client, product_type, permission_manage_products
):
    query = """
        mutation deleteProductType($id: ID!) {
            productTypeDelete(id: $id) {
                productType {
                    name
                }
            }
        }
    """
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()


def test_product_image_create_mutation(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            image {
                id
            }
        }
    }
    """
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.graphql.product.mutations.products."
            "create_product_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    image_file, image_name = create_image()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": image_name,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    product.refresh_from_db()
    product_image = product.images.last()
    assert product_image.image.file

    # The image creation should have triggered a warm-up
    mock_create_thumbnails.assert_called_once_with(product_image.pk)


def test_product_image_create_mutation_without_file(
    monkeypatch, staff_api_client, product, permission_manage_products, media_root
):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            productErrors {
                code
                field
            }
        }
    }
    """
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": "image name",
    }
    body = get_multipart_request_body(query, variables, file="", file_name="name")
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    errors = content["data"]["productImageCreate"]["productErrors"]
    assert errors[0]["field"] == "image"
    assert errors[0]["code"] == ProductErrorCode.REQUIRED.name


def test_invalid_product_image_create_mutation(
    staff_api_client, product, permission_manage_products
):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            image {
                id
                url
                sortOrder
            }
            errors {
                field
                message
            }
        }
    }
    """
    image_file, image_name = create_pdf_file_with_image_ext()
    variables = {
        "product": graphene.Node.to_global_id("Product", product.id),
        "image": image_name,
    }
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productImageCreate"]["errors"] == [
        {"field": "image", "message": "Invalid file type"}
    ]
    product.refresh_from_db()
    assert product.images.count() == 0


def test_product_image_update_mutation(
    monkeypatch, staff_api_client, product_with_image, permission_manage_products
):
    query = """
    mutation updateProductImage($imageId: ID!, $alt: String) {
        productImageUpdate(id: $imageId, input: {alt: $alt}) {
            image {
                alt
            }
        }
    }
    """

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.graphql.product.mutations.products."
            "create_product_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    image_obj = product_with_image.images.first()
    alt = "damage alt"
    variables = {
        "alt": alt,
        "imageId": graphene.Node.to_global_id("ProductImage", image_obj.id),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["productImageUpdate"]["image"]["alt"] == alt

    # We did not update the image field,
    # the image should not have triggered a warm-up
    assert mock_create_thumbnails.call_count == 0


def test_product_image_delete(
    staff_api_client, product_with_image, permission_manage_products
):
    product = product_with_image
    query = """
            mutation deleteProductImage($id: ID!) {
                productImageDelete(id: $id) {
                    image {
                        id
                        url
                    }
                }
            }
        """
    image_obj = product.images.first()
    node_id = graphene.Node.to_global_id("ProductImage", image_obj.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productImageDelete"]
    assert image_obj.image.url in data["image"]["url"]
    with pytest.raises(image_obj._meta.model.DoesNotExist):
        image_obj.refresh_from_db()
    assert node_id == data["image"]["id"]


def test_reorder_images(
    staff_api_client, product_with_images, permission_manage_products
):
    query = """
    mutation reorderImages($product_id: ID!, $images_ids: [ID]!) {
        productImageReorder(productId: $product_id, imagesIds: $images_ids) {
            product {
                id
            }
        }
    }
    """
    product = product_with_images
    images = product.images.all()
    image_0 = images[0]
    image_1 = images[1]
    image_0_id = graphene.Node.to_global_id("ProductImage", image_0.id)
    image_1_id = graphene.Node.to_global_id("ProductImage", image_1.id)
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"product_id": product_id, "images_ids": [image_1_id, image_0_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)

    # Check if order has been changed
    product.refresh_from_db()
    reordered_images = product.images.all()
    reordered_image_0 = reordered_images[0]
    reordered_image_1 = reordered_images[1]
    assert image_0.id == reordered_image_1.id
    assert image_1.id == reordered_image_0.id


ASSIGN_VARIANT_QUERY = """
    mutation assignVariantImageMutation($variantId: ID!, $imageId: ID!) {
        variantImageAssign(variantId: $variantId, imageId: $imageId) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
"""


def test_assign_variant_image(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    image = product_with_image.images.first()

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.images.first() == image


def test_assign_variant_image_from_different_product(
    staff_api_client, user_api_client, product_with_image, permission_manage_products
):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    product_with_image.pk = None
    product_with_image.slug = "product-with-image"
    product_with_image.save()

    image_2 = ProductImage.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image_2.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantImageAssign"]["errors"][0]["field"] == "imageId"

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


UNASSIGN_VARIANT_IMAGE_QUERY = """
    mutation unassignVariantImageMutation($variantId: ID!, $imageId: ID!) {
        variantImageUnassign(variantId: $variantId, imageId: $imageId) {
            errors {
                field
                message
            }
            productVariant {
                id
            }
        }
    }
"""


def test_unassign_variant_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY

    image = product_with_image.images.first()
    variant = product_with_image.variants.first()
    variant.variant_images.create(image=image)

    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.images.count() == 0


def test_unassign_not_assigned_variant_image(
    staff_api_client, product_with_image, permission_manage_products
):
    query = UNASSIGN_VARIANT_IMAGE_QUERY
    variant = product_with_image.variants.first()
    image_2 = ProductImage.objects.create(product=product_with_image)
    variables = {
        "variantId": to_global_id("ProductVariant", variant.pk),
        "imageId": to_global_id("ProductImage", image_2.pk),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    assert content["data"]["variantImageUnassign"]["errors"][0]["field"] == ("imageId")


@patch("saleor.product.tasks.update_variants_names.delay")
def test_product_type_update_changes_variant_name(
    mock_update_variants_names,
    staff_api_client,
    product_type,
    product,
    permission_manage_products,
):
    query = """
    mutation updateProductType(
        $id: ID!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $variantAttributes: [ID],
        ) {
            productTypeUpdate(
            id: $id,
            input: {
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                variantAttributes: $variantAttributes}) {
                productType {
                    id
                }
              }
            }
    """
    variant = product.variants.first()
    variant.name = "test name"
    variant.save()
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.id)

    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id("Attribute", att.id) for att in variant_attributes
    ]
    variables = {
        "id": product_type_id,
        "hasVariants": has_variants,
        "isShippingRequired": require_shipping,
        "variantAttributes": variant_attributes_ids,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    get_graphql_content(response)
    variant_attributes = set(variant_attributes)
    variant_attributes_ids = [attr.pk for attr in variant_attributes]
    mock_update_variants_names.assert_called_once_with(
        product_type.pk, variant_attributes_ids
    )


@patch("saleor.product.tasks._update_variants_names")
def test_product_update_variants_names(mock__update_variants_names, product_type):
    variant_attributes = [product_type.variant_attributes.first()]
    variant_attr_ids = [attr.pk for attr in variant_attributes]
    update_variants_names(product_type.pk, variant_attr_ids)
    assert mock__update_variants_names.call_count == 1


def test_product_variants_by_ids(user_api_client, variant):
    query = """
        query getProduct($ids: [ID!]) {
            productVariants(ids: $ids, first: 1) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)

    variables = {"ids": [variant_id]}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert data["edges"][0]["node"]["id"] == variant_id
    assert len(data["edges"]) == 1


def test_product_variants_no_ids_list(user_api_client, variant):
    query = """
        query getProductVariants {
            productVariants(first: 10) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["productVariants"]
    assert len(data["edges"]) == ProductVariant.objects.count()


@pytest.mark.parametrize(
    "product_price, variant_override, api_variant_price",
    [(100, None, 100), (100, 200, 200), (100, 0, 0)],
)
def test_product_variant_price(
    product_price, variant_override, api_variant_price, user_api_client, variant, stock
):
    # Set price override on variant that is different than product price
    product = variant.product
    product.price = Money(amount=product_price, currency="USD")
    product.save()
    if variant_override is not None:
        product.variants.update(price_override_amount=variant_override, currency="USD")
    else:
        product.variants.update(price_override_amount=None)
    # Drop other variants
    # product.variants.exclude(id=variant.pk).delete()

    query = """
        query getProductVariants($id: ID!) {
            product(id: $id) {
                variants {
                    pricing {
                        priceUndiscounted {
                            gross {
                                amount
                            }
                        }
                    }
                }
            }
        }
        """
    product_id = graphene.Node.to_global_id("Product", variant.product.id)
    variables = {"id": product_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["product"]
    variant_price = data["variants"][0]["pricing"]["priceUndiscounted"]["gross"]
    assert variant_price["amount"] == api_variant_price


def test_report_product_sales(
    staff_api_client,
    order_with_lines,
    permission_manage_products,
    permission_manage_orders,
):
    query = """
    query TopProducts($period: ReportingPeriod!) {
        reportProductSales(period: $period, first: 20) {
            edges {
                node {
                    revenue(period: $period) {
                        gross {
                            amount
                        }
                    }
                    quantityOrdered
                    sku
                }
            }
        }
    }
    """
    variables = {"period": ReportingPeriod.TODAY.name}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    edges = content["data"]["reportProductSales"]["edges"]

    node_a = edges[0]["node"]
    line_a = order_with_lines.lines.get(product_sku=node_a["sku"])
    assert node_a["quantityOrdered"] == line_a.quantity
    amount = str(node_a["revenue"]["gross"]["amount"])
    assert Decimal(amount) == line_a.quantity * line_a.unit_price_gross_amount

    node_b = edges[1]["node"]
    line_b = order_with_lines.lines.get(product_sku=node_b["sku"])
    assert node_b["quantityOrdered"] == line_b.quantity
    amount = str(node_b["revenue"]["gross"]["amount"])
    assert Decimal(amount) == line_b.quantity * line_b.unit_price_gross_amount


@pytest.mark.parametrize(
    "field, is_nested",
    (
        ("basePrice", True),
        ("purchaseCost", True),
        ("margin", True),
        ("privateMeta", True),
    ),
)
def test_product_restricted_fields_permissions(
    staff_api_client,
    permission_manage_products,
    permission_manage_orders,
    product,
    field,
    is_nested,
):
    """Ensure non-public (restricted) fields are correctly requiring
    the 'manage_products' permission.
    """
    query = """
    query Product($id: ID!) {
        product(id: $id) {
            %(field)s
        }
    }
    """ % {
        "field": field if not is_nested else "%s { __typename }" % field
    }
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert field in content["data"]["product"]


@pytest.mark.parametrize(
    "field, is_nested",
    (
        ("digitalContent", True),
        ("margin", False),
        ("costPrice", True),
        ("priceOverride", True),
        ("quantityOrdered", False),
        ("privateMeta", True),
    ),
)
def test_variant_restricted_fields_permissions(
    staff_api_client,
    permission_manage_products,
    permission_manage_orders,
    product,
    field,
    is_nested,
):
    """Ensure non-public (restricted) fields are correctly requiring
    the 'manage_products' permission.
    """
    query = """
    query ProductVariant($id: ID!) {
        productVariant(id: $id) {
            %(field)s
        }
    }
    """ % {
        "field": field if not is_nested else "%s { __typename }" % field
    }
    variant = product.variants.first()
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert field in content["data"]["productVariant"]


def test_variant_digital_content(
    staff_api_client, permission_manage_products, digital_content
):
    query = """
    query Margin($id: ID!) {
        productVariant(id: $id) {
            digitalContent{
                id
            }
        }
    }
    """
    variant = digital_content.product_variant
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    permissions = [permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert "digitalContent" in content["data"]["productVariant"]
    assert "id" in content["data"]["productVariant"]["digitalContent"]


def test_variant_availability_without_inventory_tracking(
    api_client, variant_without_inventory_tracking, settings
):
    query = """
    query variantAvailability($id: ID!) {
        productVariant(id: $id) {
            isAvailable
            stockQuantity
        }
    }
    """
    variant = variant_without_inventory_tracking
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is True
    assert variant_data["stockQuantity"] == settings.MAX_CHECKOUT_LINE_QUANTITY


def test_variant_availability_without_inventory_tracking_not_available(
    api_client, variant_without_inventory_tracking, settings
):
    query = """
    query variantAvailability($id: ID!) {
        productVariant(id: $id) {
            isAvailable
            stockQuantity
        }
    }
    """
    variant = variant_without_inventory_tracking
    variant.stocks.all().delete()
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["isAvailable"] is False
    assert variant_data["stockQuantity"] == 0


@pytest.mark.parametrize(
    "collection_filter, count",
    [
        ({"published": "PUBLISHED"}, 2),
        ({"published": "HIDDEN"}, 1),
        ({"search": "-published1"}, 1),
        ({"search": "Collection3"}, 1),
        ({"ids": [to_global_id("Collection", 2), to_global_id("Collection", 3)]}, 2),
    ],
)
def test_collections_query_with_filter(
    collection_filter,
    count,
    query_collections_with_filter,
    staff_api_client,
    permission_manage_products,
):
    Collection.objects.bulk_create(
        [
            Collection(
                id=1,
                name="Collection1",
                slug="collection-published1",
                is_published=True,
                description="Test description",
            ),
            Collection(
                id=2,
                name="Collection2",
                slug="collection-published2",
                is_published=True,
                description="Test description",
            ),
            Collection(
                id=3,
                name="Collection3",
                slug="collection-unpublished",
                is_published=False,
                description="Test description",
            ),
        ]
    )

    variables = {"filter": collection_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_collections_with_filter, variables)
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]

    assert len(collections) == count


QUERY_COLLECTIONS_WITH_SORT = """
    query ($sort_by: CollectionSortingInput!) {
        collections(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "collection_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Coll1", "Coll2", "Coll3"]),
        ({"field": "NAME", "direction": "DESC"}, ["Coll3", "Coll2", "Coll1"]),
        ({"field": "AVAILABILITY", "direction": "ASC"}, ["Coll2", "Coll1", "Coll3"]),
        ({"field": "AVAILABILITY", "direction": "DESC"}, ["Coll3", "Coll1", "Coll2"]),
        ({"field": "PRODUCT_COUNT", "direction": "ASC"}, ["Coll1", "Coll3", "Coll2"]),
        ({"field": "PRODUCT_COUNT", "direction": "DESC"}, ["Coll2", "Coll3", "Coll1"]),
    ],
)
def test_collections_query_with_sort(
    collection_sort, result_order, staff_api_client, permission_manage_products, product
):
    Collection.objects.bulk_create(
        [
            Collection(name="Coll1", slug="collection-published1", is_published=True),
            Collection(
                name="Coll2", slug="collection-unpublished2", is_published=False
            ),
            Collection(name="Coll3", slug="collection-published", is_published=True),
        ]
    )
    product.collections.add(Collection.objects.get(name="Coll2"))

    variables = {"sort_by": collection_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_COLLECTIONS_WITH_SORT, variables)
    content = get_graphql_content(response)
    collections = content["data"]["collections"]["edges"]

    for order, colllection_name in enumerate(result_order):
        assert collections[order]["node"]["name"] == colllection_name


@pytest.mark.parametrize(
    "category_filter, count",
    [
        ({"search": "slug_"}, 3),
        ({"search": "Category1"}, 1),
        ({"search": "cat1"}, 2),
        ({"search": "Subcategory_description"}, 1),
        ({"ids": [to_global_id("Category", 2), to_global_id("Category", 3)]}, 2),
    ],
)
def test_categories_query_with_filter(
    category_filter,
    count,
    query_categories_with_filter,
    staff_api_client,
    permission_manage_products,
):
    Category.objects.create(
        id=1, name="Category1", slug="slug_category1", description="Description cat1"
    )
    Category.objects.create(
        id=2, name="Category2", slug="slug_category2", description="Description cat2"
    )
    Category.objects.create(
        id=3,
        name="SubCategory",
        slug="slug_subcategory",
        parent=Category.objects.get(name="Category1"),
        description="Subcategory_description of cat1",
    )
    variables = {"filter": category_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query_categories_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["categories"]["totalCount"] == count


QUERY_CATEGORIES_WITH_SORT = """
    query ($sort_by: CategorySortingInput!) {
        categories(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "category_sort, result_order",
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Cat1", "Cat2", "SubCat", "SubSubCat"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["SubSubCat", "SubCat", "Cat2", "Cat1"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "ASC"},
            ["Cat2", "SubSubCat", "Cat1", "SubCat"],
        ),
        (
            {"field": "SUBCATEGORY_COUNT", "direction": "DESC"},
            ["SubCat", "Cat1", "SubSubCat", "Cat2"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "ASC"},
            ["Cat2", "SubCat", "SubSubCat", "Cat1"],
        ),
        (
            {"field": "PRODUCT_COUNT", "direction": "DESC"},
            ["Cat1", "SubSubCat", "SubCat", "Cat2"],
        ),
    ],
)
def test_categories_query_with_sort(
    category_sort,
    result_order,
    staff_api_client,
    permission_manage_products,
    product_type,
):
    cat1 = Category.objects.create(
        name="Cat1", slug="slug_category1", description="Description cat1"
    )
    Product.objects.create(
        name="Test",
        slug="test",
        price=Money(10, "USD"),
        product_type=product_type,
        category=cat1,
        is_published=True,
    )
    Category.objects.create(
        name="Cat2", slug="slug_category2", description="Description cat2"
    )
    Category.objects.create(
        name="SubCat",
        slug="slug_subcategory1",
        parent=Category.objects.get(name="Cat1"),
        description="Subcategory_description of cat1",
    )
    subsubcat = Category.objects.create(
        name="SubSubCat",
        slug="slug_subcategory2",
        parent=Category.objects.get(name="SubCat"),
        description="Subcategory_description of cat1",
    )
    Product.objects.create(
        name="Test2",
        slug="test2",
        price=Money(10, "USD"),
        product_type=product_type,
        category=subsubcat,
        is_published=True,
    )
    variables = {"sort_by": category_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_CATEGORIES_WITH_SORT, variables)
    content = get_graphql_content(response)
    categories = content["data"]["categories"]["edges"]

    for order, category_name in enumerate(result_order):
        assert categories[order]["node"]["name"] == category_name


@pytest.mark.parametrize(
    "product_type_filter, count",
    [
        ({"configurable": "CONFIGURABLE"}, 2),  # has_variants
        ({"configurable": "SIMPLE"}, 1),  # !has_variants
        ({"productType": "DIGITAL"}, 1),
        ({"productType": "SHIPPABLE"}, 2),  # is_shipping_required
    ],
)
def test_product_type_query_with_filter(
    product_type_filter, count, staff_api_client, permission_manage_products
):
    query = """
        query ($filter: ProductTypeFilterInput!, ) {
          productTypes(first:5, filter: $filter) {
            edges{
              node{
                id
                name
              }
            }
          }
        }
        """
    ProductType.objects.bulk_create(
        [
            ProductType(
                name="Digital Type",
                slug="digital-type",
                has_variants=True,
                is_shipping_required=False,
                is_digital=True,
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
            ),
            ProductType(
                name="Books",
                slug="books",
                has_variants=False,
                is_shipping_required=True,
                is_digital=False,
            ),
        ]
    )

    variables = {"filter": product_type_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_types = content["data"]["productTypes"]["edges"]

    assert len(product_types) == count


QUERY_PRODUCT_TYPE_WITH_SORT = """
    query ($sort_by: ProductTypeSortingInput!) {
        productTypes(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        name
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "product_type_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Digital", "Subscription", "Tools"]),
        ({"field": "NAME", "direction": "DESC"}, ["Tools", "Subscription", "Digital"]),
        # is_digital
        (
            {"field": "DIGITAL", "direction": "ASC"},
            ["Subscription", "Tools", "Digital"],
        ),
        (
            {"field": "DIGITAL", "direction": "DESC"},
            ["Digital", "Tools", "Subscription"],
        ),
        # is_shipping_required
        (
            {"field": "SHIPPING_REQUIRED", "direction": "ASC"},
            ["Digital", "Subscription", "Tools"],
        ),
        (
            {"field": "SHIPPING_REQUIRED", "direction": "DESC"},
            ["Tools", "Subscription", "Digital"],
        ),
    ],
)
def test_product_type_query_with_sort(
    product_type_sort, result_order, staff_api_client, permission_manage_products
):
    ProductType.objects.bulk_create(
        [
            ProductType(
                name="Digital",
                slug="digital",
                has_variants=True,
                is_shipping_required=False,
                is_digital=True,
            ),
            ProductType(
                name="Tools",
                slug="tools",
                has_variants=True,
                is_shipping_required=True,
                is_digital=False,
            ),
            ProductType(
                name="Subscription",
                slug="subscription",
                has_variants=False,
                is_shipping_required=False,
                is_digital=False,
            ),
        ]
    )

    variables = {"sort_by": product_type_sort}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(QUERY_PRODUCT_TYPE_WITH_SORT, variables)
    content = get_graphql_content(response)
    product_types = content["data"]["productTypes"]["edges"]

    for order, product_type_name in enumerate(result_order):
        assert product_types[order]["node"]["name"] == product_type_name


NOT_EXISTS_IDS_COLLECTIONS_QUERY = """
    query ($filter: ProductTypeFilterInput!) {
        productTypes(first: 5, filter: $filter) {
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
"""


def test_product_types_query_ids_not_exists(user_api_client, category):
    query = NOT_EXISTS_IDS_COLLECTIONS_QUERY
    variables = {"filter": {"ids": ["fTEJRuFHU6fd2RU=", "2XwnQNNhwCdEjhP="]}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response, ignore_errors=True)
    message_error = '{"ids": [{"message": "Invalid ID specified.", "code": ""}]}'

    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == message_error
    assert content["data"]["productTypes"] is None


MUTATION_BULK_PUBLISH_PRODUCTS = """
        mutation publishManyProducts($ids: [ID]!, $is_published: Boolean!) {
            productBulkPublish(ids: $ids, isPublished: $is_published) {
                count
            }
        }
    """


def test_bulk_publish_products(
    staff_api_client, product_list_unpublished, permission_manage_products
):
    product_list = product_list_unpublished
    assert not any(product.is_published for product in product_list)

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ],
        "is_published": True,
    }
    response = staff_api_client.post_graphql(
        MUTATION_BULK_PUBLISH_PRODUCTS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    product_list = Product.objects.filter(
        id__in=[product.pk for product in product_list]
    )

    assert content["data"]["productBulkPublish"]["count"] == len(product_list)
    assert all(product.is_published for product in product_list)


def test_bulk_unpublish_products(
    staff_api_client, product_list_published, permission_manage_products
):
    product_list = product_list_published
    assert all(product.is_published for product in product_list)

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ],
        "is_published": False,
    }
    response = staff_api_client.post_graphql(
        MUTATION_BULK_PUBLISH_PRODUCTS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    product_list = Product.objects.filter(
        id__in=[product.pk for product in product_list]
    )

    assert content["data"]["productBulkPublish"]["count"] == len(product_list)
    assert not any(product.is_published for product in product_list)


def test_product_base_price_permission(
    staff_api_client, permission_manage_products, product
):
    query = """
    query basePrice($productID: ID!) {
        product(id: $productID) {
            basePrice {
                amount
            }
        }
    }
    """
    product_id = graphene.Node.to_global_id("Product", product.id)

    variables = {"productID": product_id}
    permissions = [permission_manage_products]

    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)

    assert "basePrice" in content["data"]["product"]
    assert content["data"]["product"]["basePrice"]["amount"] == product.price.amount


QUERY_AVAILABLE_ATTRIBUTES = """
    query($productTypeId:ID!, $filters: AttributeFilterInput) {
      productType(id: $productTypeId) {
        availableAttributes(first: 10, filter: $filters) {
          edges {
            node {
              id
              slug
            }
          }
        }
      }
    }
"""


def test_product_type_get_unassigned_attributes(
    staff_api_client, permission_manage_products
):
    query = QUERY_AVAILABLE_ATTRIBUTES
    target_product_type, ignored_product_type = ProductType.objects.bulk_create(
        [
            ProductType(name="Type 1", slug="type-1"),
            ProductType(name="Type 2", slug="type-2"),
        ]
    )

    unassigned_attributes = list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size"),
                Attribute(slug="weight", name="Weight"),
                Attribute(slug="thickness", name="Thickness"),
            ]
        )
    )

    assigned_attributes = list(
        Attribute.objects.bulk_create(
            [Attribute(slug="color", name="Color"), Attribute(slug="type", name="Type")]
        )
    )

    # Ensure that assigning them to another product type
    # doesn't return an invalid response
    ignored_product_type.product_attributes.add(*unassigned_attributes)

    # Assign the other attributes to the target product type
    target_product_type.product_attributes.add(*assigned_attributes)

    gql_unassigned_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {
                "productTypeId": graphene.Node.to_global_id(
                    "ProductType", target_product_type.pk
                )
            },
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(gql_unassigned_attributes) == len(
        unassigned_attributes
    ), gql_unassigned_attributes

    received_ids = sorted((attr["node"]["id"] for attr in gql_unassigned_attributes))
    expected_ids = sorted(
        (
            graphene.Node.to_global_id("Attribute", attr.pk)
            for attr in unassigned_attributes
        )
    )

    assert received_ids == expected_ids


def test_product_type_filter_unassigned_attributes(
    staff_api_client, permission_manage_products, attribute_list
):
    expected_attribute = attribute_list[0]
    query = QUERY_AVAILABLE_ATTRIBUTES
    product_type = ProductType.objects.create(name="Empty Type")
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    filters = {"search": expected_attribute.name}

    found_attributes = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {"productTypeId": product_type_id, "filters": filters},
            permissions=[permission_manage_products],
        )
    )["data"]["productType"]["availableAttributes"]["edges"]

    assert len(found_attributes) == 1

    _, attribute_id = graphene.Node.from_global_id(found_attributes[0]["node"]["id"])
    assert attribute_id == str(expected_attribute.pk)


QUERY_FILTER_PRODUCT_TYPES = """
    query($filters: ProductTypeFilterInput) {
      productTypes(first: 10, filter: $filters) {
        edges {
          node {
            name
          }
        }
      }
    }
"""


@pytest.mark.parametrize(
    "search, expected_names",
    (
        ("", ["The best juices", "The best beers", "The worst beers"]),
        ("best", ["The best juices", "The best beers"]),
        ("worst", ["The worst beers"]),
        ("average", []),
    ),
)
def test_filter_product_types_by_custom_search_value(
    api_client, search, expected_names
):
    query = QUERY_FILTER_PRODUCT_TYPES

    ProductType.objects.bulk_create(
        [
            ProductType(name="The best juices", slug="best-juices"),
            ProductType(name="The best beers", slug="best-beers"),
            ProductType(name="The worst beers", slug="worst-beers"),
        ]
    )

    variables = {"filters": {"search": search}}

    results = get_graphql_content(api_client.post_graphql(query, variables))["data"][
        "productTypes"
    ]["edges"]

    assert len(results) == len(expected_names)
    matched_names = sorted([result["node"]["name"] for result in results])

    assert matched_names == sorted(expected_names)


def test_product_filter_by_attribute_values(
    staff_api_client,
    permission_manage_products,
    color_attribute,
    pink_attribute_value,
    product_with_variant_with_two_attributes,
):
    query = """
    query Products($filters: ProductFilterInput) {
      products(first: 5, filter: $filters) {
        edges {
        node {
          id
          name
          attributes {
            attribute {
              name
              slug
            }
            values {
              name
              slug
            }
          }
        }
        }
      }
    }
    """
    variables = {
        "attributes": [
            {"slug": color_attribute.slug, "values": [pink_attribute_value.slug]}
        ]
    }
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["products"]["edges"] == [
        {
            "node": {
                "attributes": [],
                "name": product_with_variant_with_two_attributes.name,
            }
        }
    ]


MUTATION_CREATE_PRODUCT_WITH_STOCKS = """
mutation createProduct(
        $productType: ID!,
        $category: ID!
        $name: String!,
        $sku: String,
        $stocks: [StockInput!],
        $basePrice: Decimal!
        $trackInventory: Boolean)
    {
        productCreate(
            input: {
                category: $category,
                productType: $productType,
                name: $name,
                sku: $sku,
                stocks: $stocks,
                trackInventory: $trackInventory,
                basePrice: $basePrice,
            })
        {
            product {
                id
                name
                variants{
                    id
                    sku
                    trackInventory
                    quantity
                    stockQuantity
                }
            }
            productErrors {
                message
                field
                code
            }
        }
    }
    """


def test_create_product_without_variant_creates_stocks(
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
    warehouse,
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
        "stocks": stocks,
        "sku": "23434",
        "trackInventory": True,
        "basePrice": Decimal("19"),
    }
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PRODUCT_WITH_STOCKS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["productCreate"]
    quantity = data["product"]["variants"][0]["stockQuantity"]
    assert quantity == 20


def test_create_product_with_variants_does_not_create_stock(
    staff_api_client, category, product_type, permission_manage_products, warehouse
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    stocks = [
        {
            "warehouse": graphene.Node.to_global_id("Warehouse", warehouse.pk),
            "quantity": 20,
        }
    ]
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
        "quantity": 8,
        "stocks": stocks,
        "sku": "23434",
        "trackInventory": True,
        "basePrice": Decimal("19"),
    }
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PRODUCT_WITH_STOCKS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    variants = content["data"]["productCreate"]["product"]["variants"]
    assert len(variants) == 0
    assert not Stock.objects.exists()


def test_create_stocks_failed(product_with_single_variant, warehouse):
    variant = product_with_single_variant.variants.first()

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]
    warehouses = [warehouse, second_warehouse]
    with pytest.raises(ValidationError):
        create_stocks(variant, stocks_data, warehouses)


def test_create_stocks(variant, warehouse):
    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.slug = "second warehouse"
    second_warehouse.pk = None
    second_warehouse.save()

    assert variant.stocks.count() == 0

    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]
    warehouses = [warehouse, second_warehouse]
    create_stocks(variant, stocks_data, warehouses)

    assert variant.stocks.count() == len(stocks_data)
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


def test_update_or_create_variant_stocks(variant, warehouses):
    Stock.objects.create(
        product_variant=variant, warehouse=warehouses[0], quantity=5,
    )
    stocks_data = [
        {"quantity": 10, "warehouse": "123"},
        {"quantity": 10, "warehouse": "321"},
    ]

    ProductVariantStocksUpdate.update_or_create_variant_stocks(
        variant, stocks_data, warehouses
    )

    variant.refresh_from_db()
    assert variant.stocks.count() == 2
    assert {stock.warehouse.pk for stock in variant.stocks.all()} == {
        warehouse.pk for warehouse in warehouses
    }
    assert {stock.quantity for stock in variant.stocks.all()} == {
        data["quantity"] for data in stocks_data
    }


def test_update_or_create_variant_stocks_empty_stocks_data(variant, warehouses):
    Stock.objects.create(
        product_variant=variant, warehouse=warehouses[0], quantity=5,
    )

    ProductVariantStocksUpdate.update_or_create_variant_stocks(variant, [], warehouses)

    variant.refresh_from_db()
    assert variant.stocks.count() == 1
    stock = variant.stocks.first()
    assert stock.warehouse == warehouses[0]
    assert stock.quantity == 5


# Because we use Scalars for Weight this test query tests only a scenario when weight
# value is passed by a variable
MUTATION_CREATE_PRODUCT_WITH_WEIGHT_GQL_VARIABLE = """
mutation createProduct(
        $productType: ID!,
        $category: ID!
        $name: String!,
        $sku: String,
        $basePrice: Decimal!
        $weight: WeightScalar)
    {
        productCreate(
            input: {
                category: $category,
                productType: $productType,
                name: $name,
                sku: $sku,
                basePrice: $basePrice,
                weight: $weight
            })
        {
            product {
                id
                weight{
                    value
                    unit
                }
            }
            productErrors {
                message
                field
                code
            }
        }
    }
    """


@pytest.mark.parametrize(
    "weight, expected_weight_value, expected_weight_unit",
    (
        ("0", 0, "kg"),
        (0, 0, "kg"),
        (11.11, 11.11, "kg"),
        (11, 11.0, "kg"),
        ("11.11", 11.11, "kg"),
        ({"value": 11.11, "unit": "kg"}, 11.11, "kg",),
        ({"value": 11, "unit": "g"}, 11.0, "g",),
        ({"value": "11.11", "unit": "ounce"}, 11.11, "oz",),
    ),
)
def test_create_product_with_weight_variable(
    weight,
    expected_weight_value,
    expected_weight_unit,
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
):
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
        "sku": "23434",
        "basePrice": Decimal("19"),
        "weight": weight,
    }
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_PRODUCT_WITH_WEIGHT_GQL_VARIABLE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    result_weight = content["data"]["productCreate"]["product"]["weight"]
    assert result_weight["value"] == expected_weight_value
    assert result_weight["unit"] == expected_weight_unit


@pytest.mark.parametrize(
    "weight, expected_weight_value, expected_weight_unit",
    (
        ("0", 0, "kg"),
        (0, 0, "kg"),
        ("11.11", 11.11, "kg"),
        ("11", 11.0, "kg"),
        ('"11.11"', 11.11, "kg"),
        ('{value: 11.11, unit: "kg"}', 11.11, "kg",),
        ('{value: 11, unit: "g"}', 11.0, "g",),
        ('{value: "11.11", unit: "ounce"}', 11.11, "oz",),
    ),
)
def test_create_product_with_weight_input(
    weight,
    expected_weight_value,
    expected_weight_unit,
    staff_api_client,
    category,
    permission_manage_products,
    product_type_without_variant,
):
    # Because we use Scalars for Weight this test query tests only a scenario when
    # weight value is passed by directly in input
    query = f"""
    mutation createProduct(
            $productType: ID!,
            $category: ID!
            $name: String!,
            $sku: String,
            $basePrice: Decimal!)
        {{
            productCreate(
                input: {{
                    category: $category,
                    productType: $productType,
                    name: $name,
                    sku: $sku,
                    basePrice: $basePrice,
                    weight: {weight}
                }})
            {{
                product {{
                    id
                    weight{{
                        value
                        unit
                    }}
                }}
                productErrors {{
                    message
                    field
                    code
                }}
            }}
        }}
    """
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_without_variant.pk
    )
    variables = {
        "category": category_id,
        "productType": product_type_id,
        "name": "Test",
        "sku": "23434",
        "basePrice": Decimal("19"),
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    result_weight = content["data"]["productCreate"]["product"]["weight"]
    assert result_weight["value"] == expected_weight_value
    assert result_weight["unit"] == expected_weight_unit
