import json

import graphene
import pytest

from .....attribute.models import Attribute
from .....product.models import Product
from ....tests.utils import get_graphql_content

PRODUCT_BULK_CREATE_MUTATION = """
    mutation ProductBulkCreate(
        $products: [ProductBulkCreateInput!]!
    ) {
        productBulkCreate(products: $products) {
            results {
                errors {
                    path
                    code
                    message
                    warehouses
                    channels
                }
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


@pytest.fixture
def attributes_without_values():
    return Attribute.objects.bulk_create(
        [Attribute(slug=f"attribute-{x}", name=f"Attribute {x}") for x in range(1000)]
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_product_bulk_create_with_base_data(
    staff_api_client,
    product_type,
    category,
    description_json,
    permission_manage_products,
    color_attribute,
    date_attribute,
    attribute_without_values,
    attributes_without_values,
):
    # given
    description_json_string = json.dumps(description_json)
    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)

    product_name_1 = "test name 1"
    product_name_2 = "test name 2"
    base_product_slug = "product-test-slug"
    product_charge_taxes = True
    product_tax_rate = "STANDARD"

    product_type.product_attributes.add(date_attribute)
    product_type.product_attributes.add(attribute_without_values)
    product_type.product_attributes.add(*attributes_without_values)

    products = [
        {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name_1,
            "description": description_json_string,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
                    "values": [
                        "#000000",
                    ],
                },
                {
                    "id": graphene.Node.to_global_id("Attribute", date_attribute.pk),
                    "values": ["2021-06-01"],
                },
            ]
            + [
                {
                    "id": graphene.Node.to_global_id(
                        "Attribute", attribute_without_values.pk
                    ),
                    "values": ["test value"],
                }
            ],
            "weight": 2,
        },
        {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name_2,
            "slug": f"{base_product_slug}-2",
            "description": description_json_string,
            "chargeTaxes": product_charge_taxes,
            "taxCode": product_tax_rate,
            "attributes": [
                {
                    "id": graphene.Node.to_global_id("Attribute", attribute.pk),
                    "values": [f"{attribute_without_values.pk}-value"],
                }
                for attribute in attributes_without_values
            ],
        },
    ]

    assert Product.objects.count() == 0

    # when
    staff_api_client.user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        PRODUCT_BULK_CREATE_MUTATION,
        {"products": products},
    )
    content = get_graphql_content(response)
    data = content["data"]["productBulkCreate"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2

    assert Product.objects.count() == 2
