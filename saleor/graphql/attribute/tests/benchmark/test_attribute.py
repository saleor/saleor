import graphene
import pytest

from .....attribute.models import AttributeTranslation, AttributeValueTranslation
from ....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_attribute(
    staff_api_client,
    color_attribute,
    permission_manage_products,
    count_queries,
):
    query = """
        query($id: ID!) {
            attribute(id: $id) {
                id
                slug
                name
                inputType
                type
                choices(first: 10) {
                    edges {
                        node {
                            slug
                            inputType
                        }
                    }
                }
                valueRequired
                visibleInStorefront
                filterableInStorefront
                filterableInDashboard
                availableInGrid
                storefrontSearchPosition
            }
        }
        """
    staff_api_client.user.user_permissions.add(permission_manage_products)
    attribute_gql_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    response = staff_api_client.post_graphql(query, {"id": attribute_gql_id})

    content = get_graphql_content(response)
    data = content["data"]["attribute"]
    assert data


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_attributes(
    staff_api_client,
    size_attribute,
    weight_attribute,
    color_attribute,
    permission_manage_products,
    count_queries,
):
    query = """
        query {
            attributes(first: 20) {
                edges {
                    node {
                        id
                        slug
                        name
                        inputType
                        type
                        choices(first: 10) {
                            edges {
                                node {
                                slug
                                inputType
                                }
                            }
                        }
                        valueRequired
                        visibleInStorefront
                        filterableInStorefront
                        filterableInDashboard
                        availableInGrid
                        storefrontSearchPosition
                    }
                }
            }
        }
        """
    staff_api_client.user.user_permissions.add(permission_manage_products)

    response = staff_api_client.post_graphql(query, {})

    content = get_graphql_content(response)
    data = content["data"]["attributes"]
    assert data


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_attribute_translation(
    staff_api_client,
    size_attribute,
    weight_attribute,
    color_attribute,
    permission_manage_products,
    count_queries,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    query = """
        {
            attributes(first: 20) {
                edges {
                    node {
                        name
                        translation(languageCode: EN) {
                            name
                        }
                    }
                }
            }
        }
    """

    attributes = [size_attribute, weight_attribute, color_attribute]
    translations = []
    for attribute in attributes:
        translations.append(
            AttributeTranslation(attribute=attribute, language_code="en")
        )
    AttributeTranslation.objects.bulk_create(translations)

    get_graphql_content(staff_api_client.post_graphql(query, {}))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_attribute_value_translation(
    staff_api_client,
    rich_text_attribute_with_many_values,
    product,
    permission_manage_products,
    count_queries,
):
    staff_api_client.user.user_permissions.add(permission_manage_products)
    query = """
        query($slug:String){
            product(slug:$slug){
                attributes{
                    values{
                        name
                        translation(languageCode:EN){
                            name
                        }
                    }
                }
            }
        }
    """

    attribute_values = rich_text_attribute_with_many_values.values.all()
    translations = []
    for attribute_value in attribute_values:
        translations.append(
            AttributeValueTranslation(
                attribute_value=attribute_value, language_code="en"
            )
        )
    AttributeValueTranslation.objects.bulk_create(translations)

    product.product_type.product_attributes.add(rich_text_attribute_with_many_values)
    associate_attribute_values_to_instance(
        product, {rich_text_attribute_with_many_values.pk: attribute_values}
    )

    variables = {"slug": product.slug}

    get_graphql_content(staff_api_client.post_graphql(query, variables))
