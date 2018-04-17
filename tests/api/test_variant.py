import json

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content


def test_create_variant(admin_client, product, product_type):
    query = """
        mutation createVar (
            $productId: ID!,
            $sku: String!,
            $priceOverride: Float, 
            $costPrice: Float,
            $quantity: Int!,
            $attributes: [AttributeValueInput]) {
                productVariantCreate(
                    productId: $productId,
                    sku: $sku,
                    priceOverride: $priceOverride, 
                    costPrice: $costPrice,
                    quantity: $quantity,
                    attributes: $attributes){
                    productVariant{
                        name
                        sku
                        attributes{
                            name
                            value
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
                        quantity
                    }
                }
            }
        
    """
    product_id = graphene.Node.to_global_id('Product', product.pk)
    sku = "1"
    price_override = 1
    cost_price = 3
    quantity = 10
    variant_slug = product_type.variant_attributes.first().slug
    variant_value = 'test-value'

    variables = json.dumps({
        'productId': product_id,
        'sku': sku,
        'quantity': quantity,
        'costPrice': cost_price,
        'priceOverride': price_override,
        'attributes': [
            {'slug': variant_slug, 'value': variant_value}]})
    response = admin_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['productVariantCreate']['productVariant']
    assert data['name'] == ""
    assert data['quantity'] == quantity
    assert data['costPrice']['amount'] == cost_price
    assert data['priceOverride']['amount'] == price_override
    assert data['sku'] == sku
    assert data['attributes'][0]['name'] == variant_slug
    assert data['attributes'][0]['value'] == variant_value
