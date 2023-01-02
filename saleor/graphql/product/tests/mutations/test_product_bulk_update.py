import datetime
import json
import os
from unittest.mock import patch
from uuid import uuid4

import graphene
import pytest
import pytz

from .....product.models import Product
from .....product.tests.utils import create_image
from ....tests.utils import (
    get_graphql_content,
    get_multipart_request_body_with_multiple_files,
)

PRODUCT_BULK_UPDATE_MUTATION = """
    mutation ProductBulkUpdate(
        $products: [ProductBulkUpdateInput!]!
    ) {
        productBulkUpdate(products: $products) {
            errors {
                field
                message
                code
                index
            }
            results {
                product{
                    id
                    name
                    slug
                    media{
                        url
                        alt
                        type
                        oembedData
                    }
                    category{
                        name
                    }
                    description
                    attributes{
                        attribute{
                          slug
                        }
                        values{
                           value
                        }
                    }
                    channelListings{
                        id
                        channel{
                            name
                        }
                    }
                    variants{
                        name
                        stocks{
                            warehouse{
                                slug
                            }
                            quantity
                        }
                    }
                }
            }
            count
        }
    }
"""


def test_product_bulk_update(
    staff_api_client,
    product_list,
    non_default_category,
    other_description_json,
    color_attribute,
    product_type,
    permission_manage_products
):
    # given
    product_1, product_2, product_3 = product_list
    product_1_id = graphene.Node.to_global_id("Product", product_1.pk)
    product_2_id = graphene.Node.to_global_id("Product", product_2.pk)
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", non_default_category.pk)
    product_1_name = "new-product-1-name"
    product_1_slug = "new-product-1-slug"
    product_2_name = "new-product-2-name"
    product_2_slug = "new-product-2-slug"
    other_description_json = json.dumps(other_description_json)
    product_charge_taxes = True
    product_tax_rate = "STANDARD"
    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.pk)
    attr_value = "Rainbow"
    metadata_key = "md key"
    metadata_value = "md value"


    prod_1_update_fields = {
        "id": product_1_id,
        "productType": product_type_id,
        "category": category_id,
        "name": product_1_name,
        "slug": product_1_slug,
        "description": other_description_json,
        "chargeTaxes": product_charge_taxes,
        "taxCode": product_tax_rate,
        "attributes": [{"id": attribute_id, "values": [attr_value]}],
        "metadata": [{"key": metadata_key, "value": metadata_value}],
        "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
    }

    prod_2_update_fields = {
        "id": product_2_id,
        "productType": product_type_id,
        "category": category_id,
        "name": product_2_name,
        "slug": product_2_slug,
        "description": other_description_json,
        "chargeTaxes": product_charge_taxes,
        "taxCode": product_tax_rate,
        "attributes": [{"id": attribute_id, "values": [attr_value]}],
        "metadata": [{"key": metadata_key, "value": metadata_value}],
        "privateMetadata": [{"key": metadata_key, "value": metadata_value}],
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_UPDATE_MUTATION,
        {"products": [prod_1_update_fields, prod_2_update_fields]},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkUpdate"]
    product_1.refresh_from_db()
    product_2.refresh_from_db()

    # then
    products = Product.objects.all()

    assert not data["errors"]
    assert data["count"] == 2
    assert data["results"][0]["product"]["name"] == product_1_name
    assert data["results"][0]["product"]["description"] == other_description_json
    assert data["results"][0]["product"]["category"]["name"] == non_default_category.name
    assert data["results"][1]["product"]["name"] == product_2_name
    assert data["results"][1]["product"]["description"] == other_description_json
    assert data["results"][1]["product"]["category"]["name"] == non_default_category.name
    assert len(products) == 2

    assert product_1.description == other_description_json
    assert product_1.category == non_default_category
    assert product_1.name == product_1_name
    assert product_1.slug == product_1_slug

    assert product_2.description == other_description_json
    assert product_2.category == non_default_category
    assert product_2.name == product_2_name
    assert product_2.slug == product_2_slug
