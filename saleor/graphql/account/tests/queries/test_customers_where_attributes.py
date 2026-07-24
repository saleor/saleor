import graphene
import pytest

from .....attribute import AttributeInputType, AttributeType
from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content

QUERY_CUSTOMERS_WITH_WHERE = """
    query ($where: CustomerWhereInput!) {
        customers(first: 10, where: $where) {
            totalCount
            edges {
                node {
                    id
                    email
                }
            }
        }
    }
"""

CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION = """
    mutation CustomerAttributeUnassign(
        $customerTypeId: ID!, $attributeIds: [ID!]!
    ) {
        customerAttributeUnassign(
            customerTypeId: $customerTypeId, attributeIds: $attributeIds
        ) {
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_filter_by_attribute_slug(
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    customer_type_with_attributes,
    loyalty_customer_attribute,
):
    # given
    permission_group_manage_users.user_set.add(staff_api_client.user)
    customer = customer_users[0]
    customer.customer_type = customer_type_with_attributes
    customer.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="gold")
    associate_attribute_values_to_instance(
        customer, {loyalty_customer_attribute.pk: [value]}
    )
    variables = {"where": {"attributes": [{"slug": loyalty_customer_attribute.slug}]}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == 1
    assert customers[0]["node"]["email"] == customer.email
    assert customers[0]["node"]["id"] == graphene.Node.to_global_id("User", customer.pk)


@pytest.mark.parametrize(
    "value_filter",
    [
        {"slug": {"eq": "gold"}},
        {"slug": {"oneOf": ["gold", "bronze"]}},
        {"name": {"eq": "Gold"}},
        {"name": {"oneOf": ["Gold", "Bronze"]}},
    ],
)
def test_filter_by_attribute_value_slug_or_name(
    value_filter,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    customer_type_with_attributes,
    loyalty_customer_attribute,
):
    # given: one customer with the matching value, another with a different
    # value of the same attribute
    permission_group_manage_users.user_set.add(staff_api_client.user)
    customer_with_gold = customer_users[0]
    customer_with_silver = customer_users[1]
    for customer in [customer_with_gold, customer_with_silver]:
        customer.customer_type = customer_type_with_attributes
        customer.save(update_fields=["customer_type"])
    gold_value = loyalty_customer_attribute.values.get(slug="gold")
    silver_value = loyalty_customer_attribute.values.get(slug="silver")
    associate_attribute_values_to_instance(
        customer_with_gold, {loyalty_customer_attribute.pk: [gold_value]}
    )
    associate_attribute_values_to_instance(
        customer_with_silver, {loyalty_customer_attribute.pk: [silver_value]}
    )
    variables = {
        "where": {
            "attributes": [
                {"slug": loyalty_customer_attribute.slug, "value": value_filter}
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == 1
    assert customers[0]["node"]["email"] == customer_with_gold.email


def test_filter_by_boolean_attribute_value(
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    customer_type,
):
    # given
    permission_group_manage_users.user_set.add(staff_api_client.user)
    newsletter_attribute = Attribute.objects.create(
        slug="newsletter",
        name="Newsletter",
        type=AttributeType.CUSTOMER_TYPE,
        input_type=AttributeInputType.BOOLEAN,
    )
    true_value = AttributeValue.objects.create(
        attribute=newsletter_attribute,
        name="Newsletter: Yes",
        slug=f"{newsletter_attribute.pk}_true",
        boolean=True,
    )
    false_value = AttributeValue.objects.create(
        attribute=newsletter_attribute,
        name="Newsletter: No",
        slug=f"{newsletter_attribute.pk}_false",
        boolean=False,
    )
    customer_type.customer_attributes.add(newsletter_attribute)
    subscribed_customer = customer_users[0]
    unsubscribed_customer = customer_users[1]
    for customer in [subscribed_customer, unsubscribed_customer]:
        customer.customer_type = customer_type
        customer.save(update_fields=["customer_type"])
    associate_attribute_values_to_instance(
        subscribed_customer, {newsletter_attribute.pk: [true_value]}
    )
    associate_attribute_values_to_instance(
        unsubscribed_customer, {newsletter_attribute.pk: [false_value]}
    )
    variables = {
        "where": {
            "attributes": [
                {"slug": newsletter_attribute.slug, "value": {"boolean": True}}
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == 1
    assert customers[0]["node"]["email"] == subscribed_customer.email


@pytest.mark.parametrize(
    ("numeric_filter", "expected_match"),
    [
        ({"eq": 10}, True),
        ({"oneOf": [10, 20]}, True),
        ({"range": {"gte": 5, "lte": 15}}, True),
        ({"eq": 20}, False),
        ({"range": {"gte": 15}}, False),
    ],
)
def test_filter_by_numeric_attribute_value(
    numeric_filter,
    expected_match,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    customer_type,
):
    # given
    permission_group_manage_users.user_set.add(staff_api_client.user)
    orders_count_attribute = Attribute.objects.create(
        slug="yearly-orders",
        name="Yearly orders",
        type=AttributeType.CUSTOMER_TYPE,
        input_type=AttributeInputType.NUMERIC,
    )
    value = AttributeValue.objects.create(
        attribute=orders_count_attribute, name="10", slug="10", numeric=10
    )
    customer_type.customer_attributes.add(orders_count_attribute)
    customer = customer_users[0]
    customer.customer_type = customer_type
    customer.save(update_fields=["customer_type"])
    associate_attribute_values_to_instance(
        customer, {orders_count_attribute.pk: [value]}
    )
    variables = {
        "where": {
            "attributes": [
                {
                    "slug": orders_count_attribute.slug,
                    "value": {"numeric": numeric_filter},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    if expected_match:
        assert len(customers) == 1
        assert customers[0]["node"]["email"] == customer.email
    else:
        assert customers == []


def test_filter_by_nonexistent_attribute_slug(
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"attributes": [{"slug": "non-existent-attribute"}]}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["customers"]["edges"] == []
    assert content["data"]["customers"]["totalCount"] == 0


@pytest.mark.parametrize("filter_by_value", [True, False])
def test_customer_not_filterable_by_attribute_after_unassign(
    filter_by_value,
    staff_api_client,
    permission_group_manage_users,
    permission_manage_customer_types_and_attributes,
    customer_users,
    customer_type,
    loyalty_customer_attribute,
):
    # given: a customer type has the attribute assigned and the customer has
    # an attribute value assigned
    permission_group_manage_users.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    customer = customer_users[0]
    customer.customer_type = customer_type
    customer.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="gold")
    associate_attribute_values_to_instance(
        customer, {loyalty_customer_attribute.pk: [value]}
    )

    attribute_filter = {"slug": loyalty_customer_attribute.slug}
    if filter_by_value:
        attribute_filter["value"] = {"slug": {"eq": value.slug}}
    where_variables = {"where": {"attributes": [attribute_filter]}}

    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_WHERE, where_variables
    )
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == 1
    assert customers[0]["node"]["email"] == customer.email

    # unassign the attribute from the customer type
    unassign_variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }
    response = staff_api_client.post_graphql(
        CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION, unassign_variables
    )
    content = get_graphql_content(response)
    assert content["data"]["customerAttributeUnassign"]["errors"] == []

    # when
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_WHERE, where_variables
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["customers"]["edges"] == []


@pytest.mark.parametrize("filter_by_value", [True, False])
def test_customer_not_filterable_by_attribute_after_customer_type_change(
    filter_by_value,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    customer_type_with_attributes,
    default_customer_type,
    loyalty_customer_attribute,
):
    # given: the customer has an attribute value assigned via their customer
    # type
    permission_group_manage_users.user_set.add(staff_api_client.user)
    customer = customer_users[0]
    customer.customer_type = customer_type_with_attributes
    customer.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="gold")
    associate_attribute_values_to_instance(
        customer, {loyalty_customer_attribute.pk: [value]}
    )

    attribute_filter = {"slug": loyalty_customer_attribute.slug}
    if filter_by_value:
        attribute_filter["value"] = {"slug": {"eq": value.slug}}
    where_variables = {"where": {"attributes": [attribute_filter]}}

    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_WHERE, where_variables
    )
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == 1
    assert customers[0]["node"]["email"] == customer.email

    # switch the customer to a type without the attribute; the value stays in
    # the database but is hidden from the API
    assert not default_customer_type.customer_attributes.filter(
        pk=loyalty_customer_attribute.pk
    ).exists()
    customer.customer_type = default_customer_type
    customer.save(update_fields=["customer_type"])
    assert customer.attributevalues.filter(value=value).exists()

    # when
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_WHERE, where_variables
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["customers"]["edges"] == []


def test_does_not_match_users_without_customer_type_for_non_default_type_attribute(
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    customer_type,
    default_customer_type,
    loyalty_customer_attribute,
):
    # given: the attribute belongs to a non-default customer type only, and
    # the customer with an assigned value has no customer type - such a
    # customer belongs to the default type, which lacks the attribute
    permission_group_manage_users.user_set.add(staff_api_client.user)
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    assert not default_customer_type.customer_attributes.filter(
        pk=loyalty_customer_attribute.pk
    ).exists()
    customer = customer_users[0]
    assert customer.customer_type_id is None
    value = loyalty_customer_attribute.values.get(slug="gold")
    associate_attribute_values_to_instance(
        customer, {loyalty_customer_attribute.pk: [value]}
    )
    variables = {"where": {"attributes": [{"slug": loyalty_customer_attribute.slug}]}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["customers"]["edges"] == []


def test_filter_matches_users_without_customer_type_via_default_type(
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    default_customer_type,
    loyalty_customer_attribute,
):
    # given: the attribute belongs to the default customer type and the
    # customer has no customer type explicitly assigned
    permission_group_manage_users.user_set.add(staff_api_client.user)
    default_customer_type.customer_attributes.add(loyalty_customer_attribute)
    customer = customer_users[0]
    assert customer.customer_type_id is None
    value = loyalty_customer_attribute.values.get(slug="gold")
    associate_attribute_values_to_instance(
        customer, {loyalty_customer_attribute.pk: [value]}
    )
    variables = {
        "where": {
            "attributes": [
                {
                    "slug": loyalty_customer_attribute.slug,
                    "value": {"slug": {"eq": value.slug}},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == 1
    assert customers[0]["node"]["email"] == customer.email
