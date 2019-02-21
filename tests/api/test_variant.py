import graphene
import pytest

from tests.api.utils import get_graphql_content


def test_fetch_variant(staff_api_client, product, permission_manage_products):
    query = """
    query ProductVariantDetails($id: ID!) {
        productVariant(id: $id) {
            id
            attributes {
                attribute {
                    id
                    name
                    slug
                    values {
                        id
                        name
                        slug
                    }
                }
                value {
                    id
                    name
                    slug
                }
            }
            costPrice {
                currency
                amount
            }
            images {
                id
            }
            name
            priceOverride {
                currency
                amount
            }
            product {
                id
            }
        }
    }
    """

    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    variables = {'id': variant_id}
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['productVariant']
    assert data['name'] == variant.name


def test_create_variant(
        staff_api_client, product, product_type, permission_manage_products):
    query = """
        mutation createVariant (
            $productId: ID!,
            $sku: String!,
            $priceOverride: Decimal,
            $costPrice: Decimal,
            $quantity: Int!,
            $attributes: [AttributeValueInput]!,
            $weight: WeightScalar,
            $trackInventory: Boolean!) {
                productVariantCreate(
                    input: {
                        product: $productId,
                        sku: $sku,
                        priceOverride: $priceOverride,
                        costPrice: $costPrice,
                        quantity: $quantity,
                        attributes: $attributes,
                        trackInventory: $trackInventory,
                        weight: $weight
                    }) {
                    productVariant {
                        name
                        sku
                        attributes {
                            attribute {
                                slug
                            }
                            value {
                                slug
                            }
                        }
                        quantity
                        priceOverride {
                            currency
                            amount
                            localized
                        }
                        costPrice {
                            currency
                            amount
                            localized
                        }
                        weight {
                            value
                            unit
                        }
                    }
                }
            }

    """
    product_id = graphene.Node.to_global_id('Product', product.pk)
    sku = "1"
    price_override = 1.32
    cost_price = 3.22
    quantity = 10
    weight = 10.22
    variant_slug = product_type.variant_attributes.first().slug
    variant_value = 'test-value'

    variables = {
        'productId': product_id,
        'sku': sku,
        'quantity': quantity,
        'costPrice': cost_price,
        'priceOverride': price_override,
        'weight': weight,
        'attributes': [
            {'slug': variant_slug, 'value': variant_value}],
        'trackInventory': True}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productVariantCreate']['productVariant']
    assert data['name'] == variant_value
    assert data['quantity'] == quantity
    assert data['costPrice']['amount'] == cost_price
    assert data['priceOverride']['amount'] == price_override
    assert data['sku'] == sku
    assert data['attributes'][0]['attribute']['slug'] == variant_slug
    assert data['attributes'][0]['value']['slug'] == variant_value
    assert data['weight']['unit'] == 'kg'
    assert data['weight']['value'] == weight


def test_create_product_variant_not_all_attributes(
        staff_api_client, product, product_type, color_attribute,
        permission_manage_products):
    query = """
            mutation createVariant (
                $productId: ID!,
                $sku: String!,
                $attributes: [AttributeValueInput]!) {
                    productVariantCreate(
                        input: {
                            product: $productId,
                            sku: $sku,
                            attributes: $attributes
                        }) {
                        errors {
                            field
                            message
                        }
                    }
                }

        """
    product_id = graphene.Node.to_global_id('Product', product.pk)
    sku = "1"
    variant_slug = product_type.variant_attributes.first().slug
    variant_value = 'test-value'
    product_type.variant_attributes.add(color_attribute)

    variables = {
        'productId': product_id,
        'sku': sku,
        'attributes': [{'slug': variant_slug, 'value': variant_value}]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    assert content['data']['productVariantCreate']['errors']
    assert content['data']['productVariantCreate']['errors'][0]['field'] == (
        'attributes:color')
    assert not product.variants.filter(sku=sku).exists()


def test_update_product_variant(
        staff_api_client, product, permission_manage_products):
    query = """
        mutation updateVariant (
            $id: ID!,
            $sku: String!,
            $costPrice: Decimal,
            $quantity: Int!,
            $trackInventory: Boolean!) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        costPrice: $costPrice,
                        quantity: $quantity,
                        trackInventory: $trackInventory
                    }) {
                    productVariant {
                        name
                        sku
                        quantity
                        costPrice {
                            currency
                            amount
                            localized
                        }
                    }
                }
            }

    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    sku = "test sku"
    cost_price = 3.3
    quantity = 123

    variables = {
        'id': variant_id,
        'sku': sku,
        'quantity': quantity,
        'costPrice': cost_price,
        'trackInventory': True}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    variant.refresh_from_db()
    content = get_graphql_content(response)
    data = content['data']['productVariantUpdate']['productVariant']
    assert data['name'] == variant.name
    assert data['quantity'] == quantity
    assert data['costPrice']['amount'] == cost_price
    assert data['sku'] == sku


def test_update_product_variant_not_all_attributes(
        staff_api_client, product, product_type, color_attribute,
        permission_manage_products):
    query = """
        mutation updateVariant (
            $id: ID!,
            $sku: String!,
            $attributes: [AttributeValueInput]!) {
                productVariantUpdate(
                    id: $id,
                    input: {
                        sku: $sku,
                        attributes: $attributes
                    }) {
                    errors {
                        field
                        message
                    }
                }
            }

    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    sku = "test sku"
    variant_slug = product_type.variant_attributes.first().slug
    variant_value = 'test-value'
    product_type.variant_attributes.add(color_attribute)

    variables = {
        'id': variant_id,
        'sku': sku,
        'attributes': [{'slug': variant_slug, 'value': variant_value}]}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    variant.refresh_from_db()
    content = get_graphql_content(response)
    assert content['data']['productVariantUpdate']['errors']
    assert content['data']['productVariantUpdate']['errors'][0]['field'] == (
        'attributes:color')
    assert not product.variants.filter(sku=sku).exists()


def test_delete_variant(staff_api_client, product, permission_manage_products):
    query = """
        mutation variantDelete($id: ID!) {
            productVariantDelete(id: $id) {
                productVariant {
                    sku
                    id
                }
              }
            }
    """
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    variables = {'id': variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)
    data = content['data']['productVariantDelete']
    assert data['productVariant']['sku'] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()


def _fetch_all_variants(client, permissions=None):
    query = """
        query fetchAllVariants {
            productVariants(first: 10) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    response = client.post_graphql(
        query, {}, permissions=permissions, check_no_permissions=False)
    content = get_graphql_content(response)
    return content['data']['productVariants']


def test_fetch_all_variants_staff_user(
        staff_api_client, unavailable_product_with_variant,
        permission_manage_products):
    data = _fetch_all_variants(
        staff_api_client, permissions=[permission_manage_products])
    variant = unavailable_product_with_variant.variants.first()
    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    assert data['totalCount'] == 1
    assert data['edges'][0]['node']['id'] == variant_id


def test_fetch_all_variants_customer(
        user_api_client, unavailable_product_with_variant):
    data = _fetch_all_variants(user_api_client)
    assert data['totalCount'] == 0


def test_fetch_all_variants_anonymous_user(
        api_client, unavailable_product_with_variant):
    data = _fetch_all_variants(api_client)
    assert data['totalCount'] == 0


def _fetch_variant(client, variant, permissions=None):
    query = """
    query ProductVariantDetails($variantId: ID!) {
        productVariant(id: $variantId) {
            id
            product {
                id
            }
        }
    }
    """
    variables = {
        'variantId': graphene.Node.to_global_id('ProductVariant', variant.id)}
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False)
    content = get_graphql_content(response)
    return content['data']['productVariant']


def test_fetch_unpublished_variant_staff_user(
        staff_api_client, unavailable_product_with_variant,
        permission_manage_products):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(
        staff_api_client, variant, permissions=[permission_manage_products])

    variant_id = graphene.Node.to_global_id('ProductVariant', variant.pk)
    product_id = graphene.Node.to_global_id(
        'Product', unavailable_product_with_variant.pk)

    assert data['id'] == variant_id
    assert data['product']['id'] == product_id


def test_fetch_unpublished_variant_customer(
        user_api_client, unavailable_product_with_variant):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(user_api_client, variant)
    assert data is None


def test_fetch_unpublished_variant_anonymous_user(
        api_client, unavailable_product_with_variant):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(api_client, variant)
    assert data is None
