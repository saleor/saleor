import graphene
import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_category_settings_update_by_staff(
    staff_api_client,
    site_settings_with_category_attributes,
    page_type_page_reference_attribute,
    page_type_product_reference_attribute,
    size_page_attribute,
    tag_page_attribute,
    permission_manage_settings,
    count_queries,
):
    query = """
        mutation CategorySettingsUpdate($input: CategorySettingsInput!) {
            categorySettingsUpdate(input: $input) {
                categorySettings {
                    attributes {
                        id
                    }
                }
                shopErrors {
                    code
                    field
                    attributes
                }
            }
        }
    """

    add_attrs = [
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [page_type_page_reference_attribute, tag_page_attribute]
    ]
    variables = {
        "input": {
            "addAttributes": add_attrs,
            "removeAttributes": [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in [page_type_product_reference_attribute]
            ],
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    get_graphql_content(response)
