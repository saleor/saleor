import json

import graphene
import pytest
from django.shortcuts import reverse
from django.utils.text import slugify
from graphql_relay import to_global_id
from prices import Money
from tests.utils import (
    create_image, create_pdf_file_with_image_ext, get_graphql_content)

from saleor.product.models import (
    Category, Collection, Product, ProductAttribute, ProductType)

from .utils import get_multipart_request_body


def test_fetch_all_products(user_api_client, product):
    query = '''
    query {
        products {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
    '''
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    num_products = Product.objects.count()
    assert content['data']['products']['totalCount'] == num_products
    assert len(content['data']['products']['edges']) == num_products


@pytest.mark.djangodb
def test_fetch_unavailable_products(user_api_client, product):
    Product.objects.update(is_published=False)
    query = '''
    query {
        products {
            totalCount
            edges {
                node {
                    id
                }
            }
        }
    }
    '''
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['products']['totalCount'] == 0
    assert not content['data']['products']['edges']


def test_product_query(admin_api_client, product):
    category = Category.objects.first()
    product = category.products.first()
    query = '''
    query {
        category(id: "%(category_id)s") {
            products {
                edges {
                    node {
                        id
                        name
                        url
                        thumbnailUrl
                        images {
                            edges {
                                node {
                                    url
                                }
                            }
                        }
                        variants {
                            edges {
                                node {
                                    name
                                    stockQuantity
                                    }
                                }
                        }
                        availability {
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
    ''' % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    assert content['data']['category'] is not None
    product_edges_data = content['data']['category']['products']['edges']
    assert len(product_edges_data) == category.products.count()
    product_data = product_edges_data[0]['node']
    assert product_data['name'] == product.name
    assert product_data['url'] == product.get_absolute_url()
    gross = product_data['availability']['priceRange']['start']['gross']
    assert float(gross['amount']) == float(product.price.amount)
    from saleor.product.utils.costs import get_product_costs_data
    purchase_cost, margin = get_product_costs_data(product)
    assert purchase_cost.start.amount == product_data[
        'purchaseCost']['start']['amount']
    assert purchase_cost.stop.amount == product_data[
        'purchaseCost']['stop']['amount']
    assert margin[0] == product_data['margin']['start']
    assert margin[1] == product_data['margin']['stop']


def test_product_with_collections(admin_api_client, product, collection):
    query = '''
        query getProduct($productID: ID!) {
            product(id: $productID) {
                collections(first: 1) {
                    edges {
                        node {
                            name
                        }
                    }
                }
            }
        }
        '''
    product.collections.add(collection)
    product.save()
    product_id = graphene.Node.to_global_id('Product', product.id)

    variables = json.dumps({'productID': product_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['product']
    assert data['collections']['edges'][0]['node']['name'] == collection.name
    assert len(data['collections']['edges']) == 1


def test_filter_product_by_category(user_api_client, product):
    category = product.category
    query = '''
    query getProducts($categoryId: ID) {
        products(category: $categoryId) {
            edges {
                node {
                    name
                }
            }
        }
    }
    '''
    response = user_api_client.post(
        reverse('api'),
        {
            'query': query,
            'variables': json.dumps(
                {
                    'categoryId': graphene.Node.to_global_id(
                        'Category', category.id)}),
            'operationName': 'getProducts'})
    content = get_graphql_content(response)
    assert 'errors' not in content
    product_data = content['data']['products']['edges'][0]['node']
    assert product_data['name'] == product.name


def test_fetch_product_by_id(user_api_client, product):
    query = '''
    query ($productId: ID!) {
        node(id: $productId) {
            ... on Product {
                name
            }
        }
    }
    '''
    response = user_api_client.post(
        reverse('api'),
        {
            'query': query,
            'variables': json.dumps(
                {
                    'productId': graphene.Node.to_global_id(
                        'Product', product.id)})})
    content = get_graphql_content(response)
    assert 'errors' not in content
    product_data = content['data']['node']
    assert product_data['name'] == product.name


def test_filter_product_by_attributes(user_api_client, product):
    product_attr = product.product_type.product_attributes.first()
    category = product.category
    attr_value = product_attr.values.first()
    filter_by = '%s:%s' % (product_attr.slug, attr_value.slug)
    query = '''
    query {
        category(id: "%(category_id)s") {
            products(attributes: ["%(filter_by)s"]) {
                edges {
                    node {
                        name
                    }
                }
            }
        }
    }
    ''' % {
        'category_id': graphene.Node.to_global_id('Category', category.id),
        'filter_by': filter_by}
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    product_data = content['data']['category']['products']['edges'][0]['node']
    assert product_data['name'] == product.name


def test_sort_products(user_api_client, product):
    # set price of the first product
    product.price = Money('10.00', 'USD')
    product.save()

    # create the second product with higher price
    product.pk = None
    product.price = Money('20.00', 'USD')
    product.save()

    query = '''
    query {
        products(sortBy: "%(sort_by)s") {
            edges {
                node {
                    price {
                        amount
                    }
                }
            }
        }
    }
    '''

    asc_price_query = query % {'sort_by': 'price'}
    response = user_api_client.post(reverse('api'), {'query': asc_price_query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    product_data = content['data']['products']['edges'][0]['node']
    price_0 = content['data']['products']['edges'][0]['node']['price']['amount']
    price_1 = content['data']['products']['edges'][1]['node']['price']['amount']
    assert price_0 < price_1

    desc_price_query = query % {'sort_by': '-price'}
    response = user_api_client.post(reverse('api'), {'query': desc_price_query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    product_data = content['data']['products']['edges'][0]['node']
    price_0 = content['data']['products']['edges'][0]['node']['price']['amount']
    price_1 = content['data']['products']['edges'][1]['node']['price']['amount']
    assert price_0 > price_1


def test_attributes_query(user_api_client, product):
    attributes = ProductAttribute.objects.prefetch_related('values')
    query = '''
    query {
        attributes {
            edges {
                node {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
                    }
                }
            }
        }
    }
    '''
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == attributes.count()


def test_attributes_in_category_query(user_api_client, product):
    category = Category.objects.first()
    query = '''
    query {
        attributes(inCategory: "%(category_id)s") {
            edges {
                node {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
                    }
                }
            }
        }
    }
    ''' % {'category_id': graphene.Node.to_global_id('Category', category.id)}
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    attributes_data = content['data']['attributes']['edges']
    assert len(attributes_data) == ProductAttribute.objects.count()


def test_create_product(
        admin_api_client, product_type, default_category, size_attribute):
    query = """
        mutation createProduct(
            $productTypeId: ID!,
            $categoryId: ID!
            $name: String!,
            $description: String!,
            $isPublished: Boolean!,
            $isFeatured: Boolean!,
            $chargeTaxes: Boolean!,
            $taxRate: String!,
            $price: Decimal!,
            $attributes: [AttributeValueInput!]) {
                productCreate(
                    input: {
                        category: $categoryId,
                        productType: $productTypeId,
                        name: $name,
                        description: $description,
                        isPublished: $isPublished,
                        isFeatured: $isFeatured,
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
                            isFeatured
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
        'Category', default_category.pk)
    product_description = 'test description'
    product_name = 'test name'
    product_isPublished = True
    product_isFeatured = False
    product_chargeTaxes = True
    product_taxRate = 'standard'
    product_price = "22.33"

    # Default attribute defined in product_type fixture
    color_attr = product_type.product_attributes.get(name='Color')
    color_attr_value = color_attr.values.first().name
    color_value_slug = color_attr.values.first().slug
    color_attr_slug = color_attr.slug
    # Add second attribute
    product_type.product_attributes.add(size_attribute)
    size_attr_slug = product_type.product_attributes.get(name='Size').slug
    non_existent_attr_value = 'The cake is a lie'

    # test creating root product
    variables = json.dumps({
        'productTypeId': product_type_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'isPublished': product_isPublished,
        'isFeatured': product_isFeatured,
        'chargeTaxes': product_chargeTaxes,
        'taxRate': product_taxRate,
        'price': product_price,
        'attributes': [
            {'slug': color_attr_slug, 'value': color_attr_value},
            {'slug': size_attr_slug, 'value': non_existent_attr_value}]})

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productCreate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['description'] == product_description
    assert data['product']['isFeatured'] == product_isFeatured
    assert data['product']['isPublished'] == product_isPublished
    assert data['product']['chargeTaxes'] == product_chargeTaxes
    assert data['product']['taxRate'] == product_taxRate
    assert data['product']['productType']['name'] == product_type.name
    assert data['product']['category']['name'] == default_category.name
    values = (
        data['product']['attributes'][0]['value']['slug'],
        data['product']['attributes'][1]['value']['slug'])
    assert slugify(non_existent_attr_value) in values
    assert color_value_slug in values


def test_update_product(
        admin_api_client, default_category, non_default_category,
        product):
    query = """
        mutation updateProduct(
            $productId: ID!,
            $categoryId: ID!,
            $name: String!,
            $description: String!,
            $isPublished: Boolean!,
            $isFeatured: Boolean!,
            $chargeTaxes: Boolean!,
            $taxRate: String!,
            $price: Decimal!,
            $attributes: [AttributeValueInput!]) {
                productUpdate(
                    id: $productId,
                    input: {
                        category: $categoryId,
                        name: $name,
                        description: $description,
                        isPublished: $isPublished,
                        isFeatured: $isFeatured,
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
                            isFeatured
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
    product_isFeatured = False
    product_chargeTaxes = True
    product_taxRate = 'standard'
    product_price = "33.12"

    variables = json.dumps({
        'productId': product_id,
        'categoryId': category_id,
        'name': product_name,
        'description': product_description,
        'isPublished': product_isPublished,
        'isFeatured': product_isFeatured,
        'chargeTaxes': product_chargeTaxes,
        'taxRate': product_taxRate,
        'price': product_price})

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productUpdate']
    assert data['errors'] == []
    assert data['product']['name'] == product_name
    assert data['product']['description'] == product_description
    assert data['product']['isFeatured'] == product_isFeatured
    assert data['product']['isPublished'] == product_isPublished
    assert data['product']['chargeTaxes'] == product_chargeTaxes
    assert data['product']['taxRate'] == product_taxRate
    assert not data['product']['category']['name'] == default_category.name


def test_delete_product(admin_api_client, product):
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
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Product', product.id)})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productDelete']
    assert data['product']['name'] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()


def test_product_type(user_api_client, product_type):
    query = """
    query {
        productTypes {
            totalCount
            edges {
                node {
                    id
                    name
                }
            }
        }
    }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    no_product_types = ProductType.objects.count()
    assert 'errors' not in content
    assert content['data']['productTypes']['totalCount'] == no_product_types
    assert len(content['data']['productTypes']['edges']) == no_product_types


def test_product_type_query(
        user_api_client, admin_api_client, product_type, product):
    query = """
            query getProductType($id: ID!) {
                productType(id: $id) {
                    name
                    products {
                        totalCount
                        edges {
                            node {
                                name
                            }
                        }
                    }
                }
            }
        """
    no_products = Product.objects.count()
    product.is_published = False
    product.save()
    variables = json.dumps({
        'id': graphene.Node.to_global_id('ProductType', product_type.id)})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']
    assert data['productType']['products']['totalCount'] == no_products - 1

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']
    assert data['productType']['products']['totalCount'] == no_products


def test_product_type_create_mutation(admin_api_client, product_type):
    query = """
    mutation createProductType(
        $name: String!,
        $hasVariants: Boolean!,
        $isShippingRequired: Boolean!,
        $productAttributes: [ID],
        $variantAttributes: [ID]) {
        productTypeCreate(
            input: {
                name: $name,
                hasVariants: $hasVariants,
                isShippingRequired: $isShippingRequired,
                productAttributes: $productAttributes,
                variantAttributes: $variantAttributes}) {
            productType {
            name
            isShippingRequired
            hasVariants
            variantAttributes {
                edges {
                node {
                    name
                }
                }
            }
            productAttributes {
                edges {
                node {
                    name
                }
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
        graphene.Node.to_global_id('ProductAttribute', att.id) for att in
        product_attributes]
    variant_attributes = product_type.variant_attributes.all()
    variant_attributes_ids = [
        graphene.Node.to_global_id('ProductAttribute', att.id) for att in
        variant_attributes]

    variables = json.dumps({
        'name': product_type_name, 'hasVariants': has_variants,
        'isShippingRequired': require_shipping,
        'productAttributes': product_attributes_ids,
        'variantAttributes': variant_attributes_ids})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productTypeCreate']
    assert data['productType']['name'] == product_type_name
    assert data['productType']['hasVariants'] == has_variants
    assert data['productType']['isShippingRequired'] == require_shipping
    no_pa = product_attributes.count()
    assert len(data['productType']['productAttributes']['edges']) == no_pa
    no_va = variant_attributes.count()
    assert len(data['productType']['variantAttributes']['edges']) == no_va


def test_product_type_update_mutation(admin_api_client, product_type):
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
                        totalCount
                    }
                    productAttributes {
                        totalCount
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
        graphene.Node.to_global_id('ProductAttribute', att.id) for att in
        product_attributes]
    variant_attributes = product_type.variant_attributes.all()

    variables = json.dumps({
        'id': product_type_id, 'name': product_type_name,
        'hasVariants': has_variants,
        'isShippingRequired': require_shipping,
        'productAttributes': product_attributes_ids})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productTypeUpdate']
    assert data['productType']['name'] == product_type_name
    assert data['productType']['hasVariants'] == has_variants
    assert data['productType']['isShippingRequired'] == require_shipping
    assert data['productType']['productAttributes']['totalCount'] == 0
    no_va = variant_attributes.count()
    assert data['productType']['variantAttributes']['totalCount'] == no_va


def test_product_type_delete_mutation(admin_api_client, product_type):
    query = """
        mutation deleteProductType($id: ID!) {
            productTypeDelete(id: $id) {
                productType {
                    name
                }
            }
        }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('ProductType', product_type.id)})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productTypeDelete']
    assert data['productType']['name'] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()


def test_product_image_create_mutation(admin_api_client, product):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            productImage {
                id
                image
                url
                sortOrder
            }
        }
    }
    """
    image_file, image_name = create_image()
    variables = {
        'product': graphene.Node.to_global_id('Product', product.id),
        'image': image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = admin_api_client.post_multipart(reverse('api'), body)
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productImageCreate']
    file_name = data['productImage']['image']
    product.refresh_from_db()
    assert product.images.first().image.file
    assert product.images.first().image.name == file_name


def test_invalid_product_image_create_mutation(admin_api_client, product):
    query = """
    mutation createProductImage($image: Upload!, $product: ID!) {
        productImageCreate(input: {image: $image, product: $product}) {
            productImage {
                id
                image
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
    response = admin_api_client.post_multipart(reverse('api'), body)
    content = get_graphql_content(response)
    assert content['data']['productImageCreate']['errors'] == [{
        'field': 'image',
        'message': 'Invalid file type'}]
    product.refresh_from_db()
    assert product.images.count() == 0


def test_product_image_update_mutation(admin_api_client, product_with_image):
    product = product_with_image
    query = """
    mutation updateProductImage($imageId: ID!, $image: Upload!, $alt: String, $product: ID!) {
        productImageUpdate(id: $imageId, input: {image: $image, alt: $alt, product: $product}) {
            productImage {
                alt
            }
        }
    }
    """
    image_obj = product_with_image.images.first()
    image = image_obj.image
    assert not image_obj.alt
    alt = 'damage alt'
    variables = {
        'product': graphene.Node.to_global_id('Product', product.id),
        'image': image.name, 'alt': alt,
        'imageId': graphene.Node.to_global_id('ProductImage', image_obj.id)}
    body = get_multipart_request_body(query, variables, image.file, image.name)
    response = admin_api_client.post_multipart(reverse('api'), body)
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productImageUpdate']
    assert data['productImage']['alt'] == alt


def test_invalid_product_image_update_mutation(
        admin_api_client, product_with_image):
    product = product_with_image
    query = """
    mutation updateProductImage($image: Upload!, $alt: String, $product: ID!, $id: ID!) {
        productImageUpdate(id: $id, input: {image: $image, alt: $alt, product: $product}) {
            productImage {
                image
            }
            errors {
                field
                message
            }
        }
    }
    """
    image_obj = product_with_image.images.first()
    image = image_obj.image
    new_image_file, new_image_name = create_pdf_file_with_image_ext()
    variables = {
        'product': graphene.Node.to_global_id('Product', product.id),
        'image': new_image_name,
        'id': graphene.Node.to_global_id('ProductImage', image_obj.id),
    }
    body = get_multipart_request_body(
        query, variables, new_image_file, new_image_name)
    response = admin_api_client.post_multipart(reverse('api'), body)
    content = get_graphql_content(response)
    assert content['data']['productImageUpdate']['errors'] == [{
        'field': 'image',
        'message': 'Invalid file type'}]
    product_with_image.refresh_from_db()
    assert product_with_image.images.count() == 1
    assert product_with_image.images.first().image == image


def test_product_image_delete(admin_api_client, product_with_image):
    product = product_with_image
    query = """
            mutation deleteProductImage($id: ID!) {
                productImageDelete(id: $id) {
                    productImage {
                        url
                    }
                }
            }
        """
    image_obj = product.images.first()
    variables = {
        'id': graphene.Node.to_global_id('ProductImage', image_obj.id)}
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productImageDelete']
    assert data['productImage']['url'] == image_obj.image.url
    with pytest.raises(image_obj._meta.model.DoesNotExist):
        image_obj.refresh_from_db()


def test_reorder_images(admin_api_client, product_with_images):
    query = """
    mutation reorderImages($product_id: ID!, $images_ids: [ID]!) {
        productImageReorder(productId: $product_id, imagesIds: $images_ids) {
            productImages {
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
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content

    # Check if order has been changed
    product.refresh_from_db()
    reordered_images = product.images.all()
    reordered_image_0 = reordered_images[0]
    reordered_image_1 = reordered_images[1]
    assert image_0.id == reordered_image_1.id
    assert image_1.id == reordered_image_0.id


def test_collections_query(user_api_client, collection):
    query = """
        query Collections {
            collections(first: 1) {
                edges {
                    node {
                        name
                        slug
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """
    response = user_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['collections']['edges'][0]['node']
    assert data['name'] == collection.name
    assert data['slug'] == collection.slug
    assert data['products']['totalCount'] == collection.products.count()


def test_create_collection(admin_api_client, product_list):
    query = """
        mutation createCollection(
            $name: String!, $slug: String!, $products: [ID], $backgroundImage: Upload!, $isPublished: Boolean!) {
            collectionCreate(
                input: {name: $name, slug: $slug, products: $products, backgroundImage: $backgroundImage, isPublished: $isPublished}) {
                collection {
                    name
                    slug
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    product_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    image_file, image_name = create_image()
    name = 'test-name'
    slug = 'test-slug'
    variables = {
        'name': name, 'slug': slug, 'products': product_ids,
        'backgroundImage': image_name, 'isPublished': True}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = admin_api_client.post_multipart(reverse('api'), body)
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['collectionCreate']['collection']
    assert data['name'] == name
    assert data['slug'] == slug
    assert data['products']['totalCount'] == len(product_ids)
    collection = Collection.objects.get(slug=slug)
    assert collection.background_image.file


def test_update_collection(admin_api_client, collection):
    query = """
        mutation updateCollection(
            $name: String!, $slug: String!, $id: ID!, $isPublished: Boolean!) {
            collectionUpdate(
                id: $id, input: {name: $name, slug: $slug, isPublished: $isPublished}) {
                collection {
                    name
                    slug
                }
            }
        }
    """
    collection_id = to_global_id('Collection', collection.id)
    name = 'new-name'
    slug = 'new-slug'
    variables = json.dumps(
        {'name': name, 'slug': slug, 'id': collection_id, 'isPublished': True})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['collectionUpdate']['collection']
    assert data['name'] == name
    assert data['slug'] == slug


def test_delete_collection(admin_api_client, collection):
    query = """
        mutation deleteCollection($id: ID!) {
            collectionDelete(id: $id) {
                collection {
                    name
                }
            }
        }
    """
    collection_id = to_global_id('Collection', collection.id)
    variables = json.dumps({'id': collection_id})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['collectionDelete']['collection']
    assert data['name'] == collection.name
    with pytest.raises(collection._meta.model.DoesNotExist):
        collection.refresh_from_db()


def test_add_products_to_collection(
        admin_api_client, collection, product_list):
    query = """
        mutation collectionAddProducts(
            $id: ID!, $products: [ID]!) {
            collectionAddProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    collection_id = to_global_id('Collection', collection.id)
    product_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    no_products_before = collection.products.count()
    variables = json.dumps(
        {'id': collection_id, 'products': product_ids})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['collectionAddProducts']['collection']
    assert data[
        'products']['totalCount'] == no_products_before + len(product_ids)


def test_remove_products_to_collection(
        admin_api_client, collection, product_list):
    query = """
        mutation collectionRemoveProducts(
            $id: ID!, $products: [ID]!) {
            collectionRemoveProducts(collectionId: $id, products: $products) {
                collection {
                    products {
                        totalCount
                    }
                }
            }
        }
    """
    collection.products.add(*product_list)
    collection_id = to_global_id('Collection', collection.id)
    product_ids = [
        to_global_id('Product', product.pk) for product in product_list]
    no_products_before = collection.products.count()
    variables = json.dumps(
        {'id': collection_id, 'products': product_ids})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['collectionRemoveProducts']['collection']
    assert data[
        'products']['totalCount'] == no_products_before - len(product_ids)
