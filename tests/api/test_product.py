import json
from datetime import datetime
from unittest.mock import Mock, patch

import graphene
import pytest
from django.utils.dateparse import parse_datetime
from django.utils.encoding import smart_text
from django.utils.text import slugify
from graphql_relay import to_global_id
from prices import Money

from saleor.graphql.core.enums import ReportingPeriod
from saleor.graphql.product.enums import StockAvailability
from saleor.graphql.product.types.products import resolve_attribute_list
from saleor.product.models import (
    Attribute, AttributeValue, Category, Collection, Product, ProductImage,
    ProductType, ProductVariant)
from saleor.product.tasks import update_variants_names
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

def test_resolve_attribute_list(color_attribute):
    value = color_attribute.values.first()
    attributes_hstore = {str(color_attribute.pk): str(value.pk)}
    res = resolve_attribute_list(attributes_hstore, Attribute.objects.all())
    assert len(res) == 1
    assert res[0].attribute.name == color_attribute.name
    assert res[0].value.name == value.name

    # test passing invalid hstore should resolve to empty list
    attr_pk = str(Attribute.objects.order_by('pk').last().pk + 1)
    val_pk = str(AttributeValue.objects.order_by('pk').last().pk + 1)
    attributes_hstore = {attr_pk: val_pk}
    res = resolve_attribute_list(attributes_hstore, Attribute.objects.all())
    assert res == []


def test_fetch_all_products(user_api_client, product):
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
    num_products = Product.objects.count()
    assert content['data']['products']['totalCount'] == num_products
    assert len(content['data']['products']['edges']) == num_products


@pytest.mark.djangodb
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
    assert content['data']['products']['totalCount'] == 0
    assert not content['data']['products']['edges']


def test_product_query(staff_api_client, product, permission_manage_products):
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
                        thumbnailUrl
                        thumbnail{
                            url
                            alt
                        }
                        images {
                            url
                        }
                        variants {
                            name
                            stockQuantity
                        }
                        isAvailable
                        price {
                            amount
                        }
                        pricing {
                            available,
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
    """ % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content['data']['category'] is not None
    product_edges_data = content['data']['category']['products']['edges']
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]['node']
    assert product_data['name'] == product.name
    assert product_data['url'] == product.get_absolute_url()
    gross = product_data['pricing']['priceRange']['start']['gross']
    assert float(gross['amount']) == float(product.price.amount)
    from saleor.product.utils.costs import get_product_costs_data
    purchase_cost, margin = get_product_costs_data(product)
    assert purchase_cost.start.amount == product_data[
        'purchaseCost']['start']['amount']
    assert purchase_cost.stop.amount == product_data[
        'purchaseCost']['stop']['amount']
    assert product_data['isAvailable'] is product.is_visible
    assert product_data['pricing']['available'] is product.is_visible
    assert product_data['price']['amount'] == product.price.amount
    assert margin[0] == product_data['margin']['start']
    assert margin[1] == product_data['margin']['stop']


@pytest.mark.parametrize(
    'stock, quantity, count', [
        ('IN_STOCK', 5, 1), ('OUT_OF_STOCK', 0, 1), ('OUT_OF_STOCK', 1, 0),
        ('IN_STOCK', 0, 0)])
def test_products_query_with_filter_stock_availability(
        stock, quantity, count, query_products_with_filter, staff_api_client,
        product, permission_manage_products):

    product.variants.update(quantity=quantity)

    variables = {'filter': {'stockAvailability': stock}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables)
    content = get_graphql_content(response)
    products = content['data']['products']['edges']

    assert len(products) == count


def test_products_query_with_filter_attributes(
        query_products_with_filter, staff_api_client, product,
        permission_manage_products):

    product_type = ProductType.objects.create(
        name='Custom Type', has_variants=True, is_shipping_required=True)
    attribute = Attribute.objects.create(
        slug='new_attr', name='Attr', product_type=product_type)
    attr_value = AttributeValue.objects.create(
        attribute=attribute, name='First', slug='first')
    second_product = product
    second_product.id = None
    second_product.product_type = product_type
    second_product.attributes = {smart_text(attribute.pk): smart_text(attr_value.pk)}
    second_product.save()

    variables = {
        'filter': {
            'attributes': [
                {'slug': attribute.slug, 'value': attr_value.slug},
            ]
        }
    }

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id(
        'Product', second_product.id)
    products = content['data']['products']['edges']

    assert len(products) == 1
    assert products[0]['node']['id'] == second_product_id
    assert products[0]['node']['name'] == second_product.name


def test_products_query_with_filter_product_type(
        query_products_with_filter, staff_api_client, product,
        permission_manage_products):
    product_type = ProductType.objects.create(
        name='Custom Type', has_variants=True, is_shipping_required=True)
    second_product = product
    second_product.id = None
    second_product.product_type = product_type
    second_product.save()

    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.id)
    variables = {'filter': {'productType': product_type_id}}

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id(
        'Product', second_product.id)
    products = content['data']['products']['edges']

    assert len(products) == 1
    assert products[0]['node']['id'] == second_product_id
    assert products[0]['node']['name'] == second_product.name


def test_products_query_with_filter_category(
        query_products_with_filter, staff_api_client, product,
        permission_manage_products):
    category = Category.objects.create(name='Custom', slug='custom')
    second_product = product
    second_product.id = None
    second_product.category = category
    second_product.save()

    category_id = graphene.Node.to_global_id('Category', category.id)
    variables = {'filter': {'categories': [category_id, ]}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id(
        'Product', second_product.id)
    products = content['data']['products']['edges']

    assert len(products) == 1
    assert products[0]['node']['id'] == second_product_id
    assert products[0]['node']['name'] == second_product.name


def test_products_query_with_filter_collection(
        query_products_with_filter, staff_api_client, product, collection,
        permission_manage_products):
    second_product = product
    second_product.id = None
    second_product.save()
    second_product.collections.add(collection)

    collection_id = graphene.Node.to_global_id('Collection', collection.id)
    variables = {'filter': {'collections': [collection_id, ]}}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id(
        'Product', second_product.id)
    products = content['data']['products']['edges']

    assert len(products) == 1
    assert products[0]['node']['id'] == second_product_id
    assert products[0]['node']['name'] == second_product.name


@pytest.mark.parametrize(
    'filter', (
            {'price': {'gte': 5.0, 'lte': 9.0}}, {'isPublished': False},
            {'search': 'Juice1'})
)
def test_products_query_with_filter(
        filter, query_products_with_filter, staff_api_client, product,
        permission_manage_products):

    second_product = product
    second_product.id = None
    second_product.name = 'Apple Juice1'
    second_product.price = Money('6.00', 'USD')
    second_product.is_published = filter.get('isPublished', True)
    second_product.save()

    variables = {'filter': filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_products_with_filter, variables)
    content = get_graphql_content(response)
    second_product_id = graphene.Node.to_global_id(
        'Product', second_product.id)
    products = content['data']['products']['edges']

    assert len(products) == 1
    assert products[0]['node']['id'] == second_product_id
    assert products[0]['node']['name'] == second_product.name


def test_product_query_search(user_api_client, product_type, category):
    blue_product = Product.objects.create(
        name='Blue Paint', price=Money('10.00', 'USD'),
        product_type=product_type, category=category)
    Product.objects.create(
        name='Red Paint', price=Money('10.00', 'USD'),
        product_type=product_type, category=category)

    query = """
    query productSearch($query: String) {
        products(query: $query, first: 10) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    response = user_api_client.post_graphql(query, {'query': 'blu p4int'})
    content = get_graphql_content(response)
    products = content['data']['products']['edges']

    assert len(products) == 1
    assert products[0]['node']['name'] == blue_product.name


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
        'productId': graphene.Node.to_global_id(
            'Product', product_with_image.pk),
        'imageId': graphene.Node.to_global_id('ProductImage', image.pk)}
    response = user_api_client.post_graphql(query, variables)
    get_graphql_content(response)


def test_product_with_collections(
        staff_api_client, product, collection, permission_manage_products):
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
    product_id = graphene.Node.to_global_id('Product', product.id)

    variables = {'productID': product_id}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['product']
    assert data['collections'][0]['name'] == collection.name
    assert len(data['collections']) == 1


def test_filter_product_by_category(user_api_client, product):
    category = product.category
    query = """
    query getProducts($categoryId: ID) {
        products(categories: [$categoryId], first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    variables = {
        'categoryId': graphene.Node.to_global_id('Category', category.id)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_data = content['data']['products']['edges'][0]['node']
    assert product_data['name'] == product.name


def test_fetch_product_by_id(user_api_client, product):
    query = """
    query ($productId: ID!) {
        node(id: $productId) {
            ... on Product {
                name
            }
        }
    }
    """
    variables = {
        'productId': graphene.Node.to_global_id('Product', product.id)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_data = content['data']['node']
    assert product_data['name'] == product.name


def _fetch_product(client, product, permissions=None):
    query = """
    query ($productId: ID!) {
        node(id: $productId) {
            ... on Product {
                name,
                isPublished
            }
        }
    }
    """
    variables = {
        'productId': graphene.Node.to_global_id('Product', product.id)}
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False)
    content = get_graphql_content(response)
    return content['data']['node']


def test_fetch_unpublished_product_staff_user(
        staff_api_client, unavailable_product, permission_manage_products):
    product_data = _fetch_product(
        staff_api_client,
        unavailable_product,
        permissions=[permission_manage_products])
    assert product_data['name'] == unavailable_product.name
    assert product_data['isPublished'] == unavailable_product.is_published


def test_fetch_unpublished_product_customer(
        user_api_client, unavailable_product):
    product_data = _fetch_product(user_api_client, unavailable_product)
    assert product_data is None


def test_fetch_unpublished_product_anonymous_user(
        api_client, unavailable_product):
    product_data = _fetch_product(api_client, unavailable_product)
    assert product_data is None


def test_filter_products_by_attributes(user_api_client, product):
    product_attr = product.product_type.product_attributes.first()
    attr_value = product_attr.values.first()
    filter_by = '%s:%s' % (product_attr.slug, attr_value.slug)
    query = """
    query {
        products(attributes: ["%(filter_by)s"], first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """ % {'filter_by': filter_by}
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    product_data = content['data']['products']['edges'][0]['node']
    assert product_data['name'] == product.name


def test_filter_products_by_categories(
        user_api_client, categories_tree, product):
    category = categories_tree.children.first()
    product.category = category
    product.save()
    query = """
    query {
        products(categories: ["%(category_id)s"], first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """ % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    product_data = content['data']['products']['edges'][0]['node']
    assert product_data['name'] == product.name


def test_filter_products_by_collections(
        user_api_client, collection, product):
    collection.products.add(product)
    query = """
    query {
        products(collections: ["%(collection_id)s"], first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """ % {'collection_id': graphene.Node.to_global_id(
        'Collection', collection.id)}
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    product_data = content['data']['products']['edges'][0]['node']
    assert product_data['name'] == product.name


def test_sort_products(user_api_client, product):
    # set price and update date of the first product
    product.price = Money('10.00', 'USD')
    product.updated_at = datetime.utcnow()
    product.save()

    # Create the second product with higher price and date
    product.pk = None
    product.price = Money('20.00', 'USD')
    product.updated_at = datetime.utcnow()
    product.save()

    query = """
    query {
        products(sortBy: %(sort_by_product_order)s, first: 2) {
            edges {
                node {
                    pricing {
                        priceRangeUndiscounted {
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

    def _get_node_price(data, node):
        return (
            data['data']['products']['edges'][node]['node']['pricing'][
                'priceRangeUndiscounted']['start']['gross']['amount'])

    asc_price_query = query % {
        'sort_by_product_order': '{field: PRICE, direction:ASC}'}
    response = user_api_client.post_graphql(asc_price_query)
    content = get_graphql_content(response)

    assert _get_node_price(content, 0) < _get_node_price(content, 1)

    desc_price_query = query % {
        'sort_by_product_order': '{field: PRICE, direction:DESC}'}
    response = user_api_client.post_graphql(desc_price_query)
    content = get_graphql_content(response)
    assert _get_node_price(content, 0) > _get_node_price(content, 1)

    asc_date_query = query % {
        'sort_by_product_order': '{field: DATE, direction:ASC}'}
    response = user_api_client.post_graphql(asc_date_query)
    content = get_graphql_content(response)
    ## parse_datetime
    date_0 = content['data']['products']['edges'][0]['node']['updatedAt']
    date_1 = content['data']['products']['edges'][1]['node']['updatedAt']
    assert parse_datetime(date_0) < parse_datetime(date_1)

    desc_date_query = query % {
        'sort_by_product_order': '{field: DATE, direction:DESC}'}
    response = user_api_client.post_graphql(desc_date_query)
    content = get_graphql_content(response)
    date_0 = content['data']['products']['edges'][0]['node']['updatedAt']
    date_1 = content['data']['products']['edges'][1]['node']['updatedAt']
    assert parse_datetime(date_0) > parse_datetime(date_1)


def test_create_product(
        staff_api_client, product_type, category, size_attribute,
        permission_manage_products):
    query = """
        mutation createProduct(
            $productTypeId: ID!,
            $categoryId: ID!,
            $name: String!,
            $description: String!,
            $descriptionJson: JSONString!,
            $isPublished: Boolean!,
            $chargeTaxes: Boolean!,
            $taxRate: TaxRateType!,
            $price: Decimal!,
            $attributes: [AttributeValueInput!]) {
                productCreate(
                    input: {
                        category: $categoryId,
                        productType: $productTypeId,
                        name: $name,
                        description: $description,
                        descriptionJson: $descriptionJson,
                        isPublished: $isPublished,
                        chargeTaxes: $chargeTaxes,
                        taxRate: $taxRate,
                        price: $price,
                        attributes: $attributes
                    }) {
                        product {
                            category {
                                name
                            }
                            description
                            descriptionJson
                            isPublished
                            chargeTaxes
                            taxRate
                            name
                            price {
                                amount
                            }
                            productType {
                                name
                            }
                            attributes {
                                attribute {
                                    slug
                                }
                                value {
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

    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.pk)
    category_id = graphene.Node.to_global_id(
        'Category', category.pk)
    product_description = 'test description'
    product_description_json = json.dumps({'content': 'description'})
    product_name = 'test name'
    product_is_published = True
    product_charge_taxes = True
    product_tax_rate = 'STANDARD'
    product_price = 22.33

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name='Color')
    color_value_slug = color_attr.values.first().slug
    color_attr_slug = color_attr.slug

    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_slug = product_type.product_attributes.get(name='Size').slug
    non_existent_attr_value = 'The cake is a lie'

    # test creating root product
    variables = {
        'productTypeId': product_type_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'descriptionJson': product_description_json,
        'isPublished': product_is_published,
        'chargeTaxes': product_charge_taxes,
        'taxRate': product_tax_rate,
        'price': product_price,
        'attributes': [
            {'slug': color_attr_slug, 'value': color_value_slug},
            {'slug': size_attr_slug, 'value': non_existent_attr_value}]}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productCreate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['description'] == product_description
    assert data['product']['descriptionJson'] == product_description_json
    assert data['product']['isPublished'] == product_is_published
    assert data['product']['chargeTaxes'] == product_charge_taxes
    assert data['product']['taxRate'] == product_tax_rate
    assert data['product']['productType']['name'] == product_type.name
    assert data['product']['category']['name'] == category.name
    values = (
        data['product']['attributes'][0]['value']['slug'],
        data['product']['attributes'][1]['value']['slug'])
    assert slugify(non_existent_attr_value) in values
    assert color_value_slug in values


QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS = """
    mutation createProduct(
        $productTypeId: ID!,
        $categoryId: ID!
        $name: String!,
        $description: String!,
        $price: Decimal!,
        $sku: String,
        $quantity: Int,
        $trackInventory: Boolean)
    {
        productCreate(
            input: {
                category: $categoryId,
                productType: $productTypeId,
                name: $name,
                description: $description,
                price: $price,
                sku: $sku,
                quantity: $quantity,
                trackInventory: $trackInventory
            })
        {
            product {
                id
                name
                variants{
                    id
                    sku
                    quantity
                    trackInventory
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
        staff_api_client, product_type_without_variant, category,
        permission_manage_products):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.pk)
    category_id = graphene.Node.to_global_id(
        'Category', category.pk)
    product_name = 'test name'
    product_description = 'description'
    product_price = 10
    sku = 'sku'
    quantity = 1
    track_inventory = True

    variables = {
        'productTypeId': product_type_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'price': product_price,
        'sku': sku,
        'quantity': quantity,
        'trackInventory': track_inventory}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productCreate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['productType']['name'] == product_type.name
    assert data['product']['category']['name'] == category.name
    assert data['product']['variants'][0]['sku'] == sku
    assert data['product']['variants'][0]['quantity'] == quantity
    assert data['product']['variants'][0]['trackInventory'] == track_inventory


def test_create_product_without_variants_sku_validation(
        staff_api_client, product_type_without_variant, category,
        permission_manage_products):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.pk)
    category_id = graphene.Node.to_global_id(
        'Category', category.pk)
    product_name = 'test name'
    product_description = 'description'
    product_price = 10
    quantity = 1
    track_inventory = True

    variables = {
        'productTypeId': product_type_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'price': product_price,
        'sku': None,
        'quantity': quantity,
        'trackInventory': track_inventory}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productCreate']
    assert data['errors'][0]['field'] == 'sku'
    assert data['errors'][0]['message'] == 'This field cannot be blank.'


def test_create_product_without_variants_sku_duplication(
        staff_api_client, product_type_without_variant, category,
        permission_manage_products, product_with_default_variant):
    query = QUERY_CREATE_PRODUCT_WITHOUT_VARIANTS

    product_type = product_type_without_variant
    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.pk)
    category_id = graphene.Node.to_global_id(
        'Category', category.pk)
    product_name = 'test name'
    product_description = 'description'
    product_price = 10
    quantity = 1
    track_inventory = True
    sku = '1234'

    variables = {
        'productTypeId': product_type_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'price': product_price,
        'sku': sku,
        'quantity': quantity,
        'trackInventory': track_inventory}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productCreate']
    assert data['errors'][0]['field'] == 'sku'
    assert data['errors'][0][
               'message'] == 'Product with this SKU already exists.'


def test_product_create_without_product_type(
        staff_api_client, category, permission_manage_products):
    query = """
    mutation createProduct($categoryId: ID!) {
        productCreate(input: {
                name: "Product",
                price: "2.5",
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

    category_id = graphene.Node.to_global_id('Category', category.id)
    response = staff_api_client.post_graphql(
        query, {'categoryId': category_id},
        permissions=[permission_manage_products])
    errors = get_graphql_content(response)['data']['productCreate']['errors']

    assert errors[0]['field'] == 'productType'
    assert errors[0]['message'] == 'This field cannot be null.'


def test_update_product(
        staff_api_client, category, non_default_category, product,
        permission_manage_products):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $categoryId: ID!,
            $name: String!,
            $description: String!,
            $isPublished: Boolean!,
            $chargeTaxes: Boolean!,
            $taxRate: TaxRateType!,
            $price: Decimal!,
            $attributes: [AttributeValueInput!]) {
                productUpdate(
                    id: $productId,
                    input: {
                        category: $categoryId,
                        name: $name,
                        description: $description,
                        isPublished: $isPublished,
                        chargeTaxes: $chargeTaxes,
                        taxRate: $taxRate,
                        price: $price,
                        attributes: $attributes
                    }) {
                        product {
                            category {
                                name
                            }
                            description
                            isPublished
                            chargeTaxes
                            taxRate
                            name
                            price {
                                amount
                            }
                            productType {
                                name
                            }
                            attributes {
                                attribute {
                                    name
                                }
                                value {
                                    name
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
    product_id = graphene.Node.to_global_id('Product', product.pk)
    category_id = graphene.Node.to_global_id(
        'Category', non_default_category.pk)
    product_description = 'updated description'
    product_name = 'updated name'
    product_isPublished = True
    product_chargeTaxes = True
    product_taxRate = 'STANDARD'
    product_price = "33.12"

    variables = {
        'productId': product_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'isPublished': product_isPublished,
        'chargeTaxes': product_chargeTaxes,
        'taxRate': product_taxRate,
        'price': product_price}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productUpdate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['description'] == product_description
    assert data['product']['isPublished'] == product_isPublished
    assert data['product']['chargeTaxes'] == product_chargeTaxes
    assert data['product']['taxRate'] == product_taxRate
    assert not data['product']['category']['name'] == category.name


def test_update_product_without_variants(
        staff_api_client, product_with_default_variant,
        permission_manage_products):
    query = """
    mutation updateProduct(
        $productId: ID!,
        $sku: String,
        $quantity: Int,
        $trackInventory: Boolean,
        $description: String)
    {
        productUpdate(
            id: $productId,
            input: {
                sku: $sku,
                quantity: $quantity,
                trackInventory: $trackInventory,
                description: $description
            })
        {
            product {
                id
                variants{
                    id
                    sku
                    quantity
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
    product_id = graphene.Node.to_global_id('Product', product.pk)
    product_sku = "test_sku"
    product_quantity = 10
    product_track_inventory = False
    product_description = "test description"

    variables = {
        'productId': product_id,
        'sku': product_sku,
        'quantity': product_quantity,
        'trackInventory': product_track_inventory,
        'description': product_description}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productUpdate']
    assert data['errors'] == []
    product = data['product']['variants'][0]
    assert product['sku'] == product_sku
    assert product['quantity'] == product_quantity
    assert product['trackInventory'] == product_track_inventory


def test_update_product_without_variants_sku_duplication(
        staff_api_client, product_with_default_variant,
        permission_manage_products, product):
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
    product_id = graphene.Node.to_global_id('Product', product.pk)
    product_sku = "123"

    variables = {
        'productId': product_id,
        'sku': product_sku}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productUpdate']
    assert data['errors']
    assert data['errors'][0]['field'] == 'sku'
    assert data['errors'][0][
               'message'] == 'Product with this SKU already exists.'


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
    node_id = graphene.Node.to_global_id('Product', product.id)
    variables = {'id': node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productDelete']
    assert data['product']['name'] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data['product']['id']


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
    assert content['data']['productTypes']['totalCount'] == no_product_types
    assert len(content['data']['productTypes']['edges']) == no_product_types


def test_product_type_query(
        user_api_client, staff_api_client, product_type, product,
        permission_manage_products):
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
                }
            }
        """
    no_products = Product.objects.count()
    product.is_published = False
    product.save()
    variables = {
        'id': graphene.Node.to_global_id('ProductType', product_type.id)}

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']
    assert data['productType']['products']['totalCount'] == no_products - 1

    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']
    assert data['productType']['products']['totalCount'] == no_products
    assert data['productType']['taxRate'] == product_type.tax_rate.upper()


def test_product_type_create_mutation(
        staff_api_client, product_type, permission_manage_products):
    query = """
    mutation createProductType(
        $name: String!,
        $taxRate: TaxRateType!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $productAttributes: [ID],
        $variantAttributes: [ID]) {
        productTypeCreate(
            input: {
                name: $name,
                taxRate: $taxRate,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes,
                variantAttributes: $variantAttributes}) {
            productType {
            name
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
    product_type_name = 'test type'
    has_variants = True
    require_shipping = True
    product_attributes = product_type.product_attributes.all()
    product_attributes_ids = [
        graphene.Node.to_global_id('Attribute', att.id) for att in
        product_attributes]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id('Attribute', att.id) for att in
        variant_attributes]

    variables = {
        'name': product_type_name, 'hasVariants': has_variants,
        'taxRate': 'STANDARD',
        'isShippingRequired': require_shipping,
        'productAttributes': product_attributes_ids,
        'variantAttributes': variant_attributes_ids}
    initial_count = ProductType.objects.count()
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert ProductType.objects.count() == initial_count + 1
    data = content['data']['productTypeCreate']['productType']
    assert data['name'] == product_type_name
    assert data['hasVariants'] == has_variants
    assert data['isShippingRequired'] == require_shipping

    pa = product_attributes[0]
    assert data['productAttributes'][0]['name'] == pa.name
    pa_values = data['productAttributes'][0]['values']
    assert sorted([value['name'] for value in pa_values]) == sorted(
        [value.name for value in pa.values.all()])

    va = variant_attributes[0]
    assert data['variantAttributes'][0]['name'] == va.name
    va_values = data['variantAttributes'][0]['values']
    assert sorted([value['name'] for value in va_values]) == sorted(
        [value.name for value in va.values.all()])

    new_instance = ProductType.objects.latest('pk')
    assert new_instance.tax_rate == 'standard'


def test_product_type_update_mutation(
        staff_api_client, product_type, permission_manage_products):
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
    product_type_name = 'test type updated'
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.id)

    # Test scenario: remove all product attributes using [] as input
    # but do not change variant attributes
    product_attributes = []
    product_attributes_ids = [
        graphene.Node.to_global_id('Attribute', att.id) for att in
        product_attributes]
    variant_attributes = product_type.variant_attributes.all()

    variables = {
        'id': product_type_id, 'name': product_type_name,
        'hasVariants': has_variants,
        'isShippingRequired': require_shipping,
        'productAttributes': product_attributes_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productTypeUpdate']['productType']
    assert data['name'] == product_type_name
    assert data['hasVariants'] == has_variants
    assert data['isShippingRequired'] == require_shipping
    assert not data['productAttributes']
    assert len(data['variantAttributes']) == (
        variant_attributes.count())


def test_product_type_delete_mutation(
        staff_api_client, product_type, permission_manage_products):
    query = """
        mutation deleteProductType($id: ID!) {
            productTypeDelete(id: $id) {
                productType {
                    name
                }
            }
        }
    """
    variables = {
        'id': graphene.Node.to_global_id('ProductType', product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productTypeDelete']
    assert data['productType']['name'] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()


def test_product_image_create_mutation(
        monkeypatch, staff_api_client, product, permission_manage_products,
        media_root):
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
        ('saleor.graphql.product.mutations.products.'
         'create_product_thumbnails.delay'),
        mock_create_thumbnails)

    image_file, image_name = create_image()
    variables = {
        'product': graphene.Node.to_global_id('Product', product.id),
        'image': image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    get_graphql_content(response)
    product.refresh_from_db()
    product_image = product.images.last()
    assert product_image.image.file

    # The image creation should have triggered a warm-up
    mock_create_thumbnails.assert_called_once_with(product_image.pk)


def test_invalid_product_image_create_mutation(
        staff_api_client, product, permission_manage_products):
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
        'product': graphene.Node.to_global_id('Product', product.id),
        'image': image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(
        body, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert content['data']['productImageCreate']['errors'] == [{
        'field': 'image',
        'message': 'Invalid file type'}]
    product.refresh_from_db()
    assert product.images.count() == 0


def test_product_image_update_mutation(
        monkeypatch,
        staff_api_client, product_with_image, permission_manage_products):
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
        ('saleor.graphql.product.mutations.products.'
         'create_product_thumbnails.delay'),
        mock_create_thumbnails)

    image_obj = product_with_image.images.first()
    alt = 'damage alt'
    variables = {
        'alt': alt,
        'imageId': graphene.Node.to_global_id('ProductImage', image_obj.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert content['data']['productImageUpdate']['image']['alt'] == alt

    # We did not update the image field,
    # the image should not have triggered a warm-up
    assert mock_create_thumbnails.call_count == 0


def test_product_image_delete(
        staff_api_client, product_with_image, permission_manage_products):
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
    node_id = graphene.Node.to_global_id('ProductImage', image_obj.id)
    variables = {'id': node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productImageDelete']
    assert image_obj.image.url in data['image']['url']
    with pytest.raises(image_obj._meta.model.DoesNotExist):
        image_obj.refresh_from_db()
    assert node_id == data['image']['id']


def test_reorder_images(
        staff_api_client, product_with_images, permission_manage_products):
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
    image_0_id = graphene.Node.to_global_id('ProductImage', image_0.id)
    image_1_id = graphene.Node.to_global_id('ProductImage', image_1.id)
    product_id = graphene.Node.to_global_id('Product', product.id)

    variables = {
        'product_id': product_id, 'images_ids': [image_1_id, image_0_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
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
        staff_api_client, user_api_client, product_with_image,
        permission_manage_products):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    image = product_with_image.images.first()

    variables = {
        'variantId': to_global_id('ProductVariant', variant.pk),
        'imageId': to_global_id('ProductImage', image.pk)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.images.first() == image


def test_assign_variant_image_from_different_product(
        staff_api_client, user_api_client, product_with_image,
        permission_manage_products):
    query = ASSIGN_VARIANT_QUERY
    variant = product_with_image.variants.first()
    product_with_image.pk = None
    product_with_image.save()

    image_2 = ProductImage.objects.create(product=product_with_image)
    variables = {
        'variantId': to_global_id('ProductVariant', variant.pk),
        'imageId': to_global_id('ProductImage', image_2.pk)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert content['data']['variantImageAssign']['errors'][0][
               'field'] == 'imageId'

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
        staff_api_client, product_with_image, permission_manage_products):
    query = UNASSIGN_VARIANT_IMAGE_QUERY

    image = product_with_image.images.first()
    variant = product_with_image.variants.first()
    variant.variant_images.create(image=image)

    variables = {
        'variantId': to_global_id('ProductVariant', variant.pk),
        'imageId': to_global_id('ProductImage', image.pk)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    get_graphql_content(response)
    variant.refresh_from_db()
    assert variant.images.count() == 0


def test_unassign_not_assigned_variant_image(
        staff_api_client, product_with_image, permission_manage_products):
    query = UNASSIGN_VARIANT_IMAGE_QUERY
    variant = product_with_image.variants.first()
    image_2 = ProductImage.objects.create(product=product_with_image)
    variables = {
        'variantId': to_global_id('ProductVariant', variant.pk),
        'imageId': to_global_id('ProductImage', image_2.pk)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert content['data']['variantImageUnassign']['errors'][0]['field'] == (
        'imageId')


@patch('saleor.product.tasks.update_variants_names.delay')
def test_product_type_update_changes_variant_name(
        mock_update_variants_names, staff_api_client, product_type,
        product, permission_manage_products):
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
    variant.name = 'test name'
    variant.save()
    has_variants = True
    require_shipping = False
    product_type_id = graphene.Node.to_global_id(
        'ProductType', product_type.id)

    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id('Attribute', att.id) for att in
        variant_attributes]
    variables = {
        'id': product_type_id,
        'hasVariants': has_variants,
        'isShippingRequired': require_shipping,
        'variantAttributes': variant_attributes_ids}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    get_graphql_content(response)
    variant_attributes = set(variant_attributes)
    variant_attributes_ids = [attr.pk for attr in variant_attributes]
    mock_update_variants_names.assert_called_once_with(
        product_type.pk, variant_attributes_ids)


@patch('saleor.product.tasks._update_variants_names')
def test_product_update_variants_names(mock__update_variants_names,
                                       product_type):
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
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.id)

    variables = {'ids': [variant_id]}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['productVariants']
    assert data['edges'][0]['node']['id'] == variant_id
    assert len(data['edges']) == 1


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
    data = content['data']['productVariants']
    assert len(data['edges']) == ProductVariant.objects.count()


@pytest.mark.parametrize('product_price, variant_override, api_variant_price',
                         [
                             (100, None, 100),
                             (100, 200, 200),
                             (100, 0, 0)
                         ])
def test_product_variant_price(
        product_price, variant_override, api_variant_price,
        user_api_client, variant):
    # Set price override on variant that is different than product price
    product = variant.product
    product.price = Money(amount=product_price, currency='USD')
    product.save()
    if variant_override is not None:
        product.variants.update(
            price_override=Money(amount=variant_override, currency='USD'))
    else:
        product.variants.update(price_override=None)
    # Drop other variants
    # product.variants.exclude(id=variant.pk).delete()

    query = """
        query getProductVariants($id: ID!) {
            product(id: $id) {
                variants {
                    price {
                        amount
                    }
                }
            }
        }
        """
    product_id = graphene.Node.to_global_id('Product', variant.product.id)
    variables = {'id': product_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['product']
    variant_price = data['variants'][0]['price']
    assert variant_price['amount'] == api_variant_price


def test_stock_availability_filter(user_api_client, product):
    query = """
    query Products($stockAvailability: StockAvailability) {
        products(stockAvailability: $stockAvailability, first: 1) {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
    """

    # fetch products in stock
    variables = {'stockAvailability': StockAvailability.IN_STOCK.name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['products']['totalCount'] == 1

    # fetch out of stock
    variables = {'stockAvailability': StockAvailability.OUT_OF_STOCK.name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['products']['totalCount'] == 0

    # Change product stock availability and test again
    product.variants.update(quantity=0)

    # There should be no products in stock
    variables = {'stockAvailability': StockAvailability.IN_STOCK.name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content['data']['products']['totalCount'] == 0


def test_report_product_sales(
        staff_api_client, order_with_lines, permission_manage_products,
        permission_manage_orders):
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
    variables = {'period': ReportingPeriod.TODAY.name}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    edges = content['data']['reportProductSales']['edges']

    node_a = edges[0]['node']
    line_a = order_with_lines.lines.get(product_sku=node_a['sku'])
    assert node_a['quantityOrdered'] == line_a.quantity
    assert (
            node_a['revenue']['gross']['amount'] ==
            line_a.quantity * line_a.unit_price_gross.amount)

    node_b = edges[1]['node']
    line_b = order_with_lines.lines.get(product_sku=node_b['sku'])
    assert node_b['quantityOrdered'] == line_b.quantity
    assert (
            node_b['revenue']['gross']['amount'] ==
            line_b.quantity * line_b.unit_price_gross.amount)


def test_variant_revenue_permissions(
        staff_api_client, permission_manage_products,
        permission_manage_orders, product):
    query = """
    query VariantRevenue($id: ID!) {
        productVariant(id: $id) {
            revenue(period: TODAY) {
                gross {
                    localized
                }
            }
        }
    }
    """
    variant = product.variants.first()
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.pk)}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert content['data']['productVariant']['revenue']


def test_variant_quantity_permissions(
        staff_api_client, permission_manage_products, product):
    query = """
    query Quantity($id: ID!) {
        productVariant(id: $id) {
            quantity
        }
    }
    """
    variant = product.variants.first()
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.pk)}
    permissions = [permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert 'quantity' in content['data']['productVariant']


def test_variant_quantity_ordered_permissions(
        staff_api_client, permission_manage_products,
        permission_manage_orders, product):
    query = """
    query QuantityOrdered($id: ID!) {
        productVariant(id: $id) {
            quantityOrdered
        }
    }
    """
    variant = product.variants.first()
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.pk)}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert 'quantityOrdered' in content['data']['productVariant']


def test_variant_quantity_allocated_permissions(
        staff_api_client, permission_manage_products,
        permission_manage_orders, product):
    query = """
    query QuantityAllocated($id: ID!) {
        productVariant(id: $id) {
            quantityAllocated
        }
    }
    """
    variant = product.variants.first()
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.pk)}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert 'quantityAllocated' in content['data']['productVariant']


def test_variant_margin_permissions(
        staff_api_client, permission_manage_products,
        permission_manage_orders, product):
    query = """
    query Margin($id: ID!) {
        productVariant(id: $id) {
            margin
        }
    }
    """
    variant = product.variants.first()
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.pk)}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert 'margin' in content['data']['productVariant']


def test_variant_digital_content(
        staff_api_client, permission_manage_products, digital_content):
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
    variables = {
        'id': graphene.Node.to_global_id('ProductVariant', variant.pk)}
    permissions = [permission_manage_products, ]
    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)
    assert 'digitalContent' in content['data']['productVariant']
    assert 'id' in content['data']['productVariant']['digitalContent']


@pytest.mark.parametrize('collection_filter, count', [
    ({'published': 'PUBLISHED'}, 2),
    ({'published': 'HIDDEN'}, 1),
    ({'search': '-published1'}, 1),
    ({'search': 'Collection3'}, 1)
])
def test_collections_query_with_filter(
        collection_filter, count, query_collections_with_filter,
        staff_api_client, permission_manage_products):
    Collection.objects.bulk_create([
        Collection(
            name='Collection1', slug='collection-published1',
            is_published=True, description='Test description'),
        Collection(
            name='Collection2', slug='collection-published2',
            is_published=True, description='Test description'),
        Collection(
            name='Collection3', slug='collection-unpublished',
            is_published=False, description='Test description')
    ])

    variables = {'filter': collection_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        query_collections_with_filter, variables)
    content = get_graphql_content(response)
    collections = content['data']['collections']['edges']

    assert len(collections) == count


@pytest.mark.parametrize('collection_filter, count', [
    ({'configurable': 'CONFIGURABLE'}, 2),  # has_variants
    ({'configurable': 'SIMPLE'}, 1),  # !has_variants
    ({'productType': 'DIGITAL'}, 1),
    ({'productType': 'SHIPPABLE'}, 2)  # is_shipping_required
])
def test_product_type_query_with_filter(
        collection_filter, count, staff_api_client,
        permission_manage_products):
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
    ProductType.objects.bulk_create([
        ProductType(
            name='Digital Type', has_variants=True, is_shipping_required=False,
            is_digital=True),
        ProductType(
            name='Tools', has_variants=True, is_shipping_required=True,
            is_digital=False),
        ProductType(
            name='Books', has_variants=False, is_shipping_required=True,
            is_digital=False)
    ])

    variables = {'filter': collection_filter}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    product_types = content['data']['productTypes']['edges']

    assert len(product_types) == count



MUTATION_BULK_PUBLISH_PRODUCTS = """
        mutation publishManyProducts($ids: [ID]!, $is_published: Boolean!) {
            productBulkPublish(ids: $ids, isPublished: $is_published) {
                count
            }
        }
    """


def test_bulk_publish_products(
        staff_api_client, product_list_unpublished,
        permission_manage_products):
    product_list = product_list_unpublished
    assert not any(product.is_published for product in product_list)

    variables = {'ids': [
        graphene.Node.to_global_id('Product', product.id)
        for product in product_list], 'is_published': True}
    response = staff_api_client.post_graphql(
        MUTATION_BULK_PUBLISH_PRODUCTS, variables,
        permissions=[permission_manage_products])
    content = get_graphql_content(response)
    product_list = Product.objects.filter(
        id__in=[product.pk for product in product_list])

    assert content['data']['productBulkPublish']['count'] == len(product_list)
    assert all(product.is_published for product in product_list)


def test_bulk_unpublish_products(
        staff_api_client, product_list_published,
        permission_manage_products):
    product_list = product_list_published
    assert all(product.is_published for product in product_list)

    variables = {'ids': [
        graphene.Node.to_global_id('Product', product.id)
        for product in product_list], 'is_published': False}
    response = staff_api_client.post_graphql(
        MUTATION_BULK_PUBLISH_PRODUCTS, variables,
        permissions=[permission_manage_products])
    content = get_graphql_content(response)
    product_list = Product.objects.filter(
        id__in=[product.pk for product in product_list])

    assert content['data']['productBulkPublish']['count'] == len(
        product_list)
    assert not any(product.is_published for product in product_list)


def test_product_base_price_permission(
        staff_api_client, permission_manage_products, product):
    query = """
    query basePrice($productID: ID!) {
        product(id: $productID) {
            basePrice {
                amount
            }
        }
    }
    """
    product_id = graphene.Node.to_global_id('Product', product.id)

    variables = {'productID': product_id}
    permissions = [permission_manage_products]

    response = staff_api_client.post_graphql(query, variables, permissions)
    content = get_graphql_content(response)

    assert 'basePrice' in content['data']['product']
    assert (
        content['data']['product']['basePrice'][
            'amount'] == product.price.amount)
