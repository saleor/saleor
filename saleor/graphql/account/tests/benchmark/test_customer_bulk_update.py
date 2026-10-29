import graphene
import pytest

from .....account.models import User
from ....tests.utils import get_graphql_content
from ..bulk_mutations.test_customer_bulk_update import (
    CUSTOMER_BULK_UPDATE_ATTRIBUTES_MUTATION,
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_customer_bulk_update_with_attributes(
    staff_api_client,
    permission_manage_users,
    customer_users,
    customer_type_with_attributes,
    loyalty_customer_attribute,
    description_customer_attribute,
    default_customer_type,
    count_queries,
):
    # given: a row changing the type, a row keeping the user's current type,
    # and typeless users whose values validate against the default type
    default_customer_type.customer_attributes.add(loyalty_customer_attribute)
    retyped_user, typed_user, typeless_user = customer_users
    typed_user.customer_type = customer_type_with_attributes
    typed_user.save(update_fields=["customer_type"])
    typeless_user.customer_type = None
    typeless_user.save(update_fields=["customer_type"])
    typeless_users = [typeless_user] + list(
        User.objects.bulk_create(
            [
                User(email="typeless-1@example.com", is_active=True),
                User(email="typeless-2@example.com", is_active=True),
            ]
        )
    )

    loyalty_id = graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
    description_id = graphene.Node.to_global_id(
        "Attribute", description_customer_attribute.pk
    )
    gold = loyalty_customer_attribute.values.get(slug="gold")
    gold_id = graphene.Node.to_global_id("AttributeValue", gold.pk)
    loyalty_input = {"id": loyalty_id, "dropdown": {"id": gold_id}}
    description_input = {"id": description_id, "plainText": "Benchmark customer."}
    customers_input = [
        {
            "id": graphene.Node.to_global_id("User", retyped_user.pk),
            "input": {
                "customerType": graphene.Node.to_global_id(
                    "CustomerType", customer_type_with_attributes.pk
                ),
                "attributes": [loyalty_input, description_input],
            },
        },
        {
            "id": graphene.Node.to_global_id("User", typed_user.pk),
            "input": {"attributes": [loyalty_input, description_input]},
        },
    ] + [
        {
            "id": graphene.Node.to_global_id("User", user.pk),
            "input": {"attributes": [loyalty_input]},
        }
        for user in typeless_users
    ]
    variables = {"customers": customers_input}
    staff_api_client.user.user_permissions.add(permission_manage_users)

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_BULK_UPDATE_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]
    assert data["count"] == len(customers_input)
    assert all(not result["errors"] for result in data["results"])
