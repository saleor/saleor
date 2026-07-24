import graphene

from .....attribute.models import AssignedUserAttributeValue
from ....tests.utils import assert_no_permission, get_graphql_content

USER_ASSIGNED_ATTRIBUTES_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            assignedAttributes {
                attribute {
                    slug
                }
                ... on AssignedSingleChoiceAttribute {
                    value {
                        slug
                    }
                }
            }
        }
    }
"""

ME_ASSIGNED_ATTRIBUTES_QUERY = """
    query Me {
        me {
            assignedAttributes {
                attribute {
                    slug
                }
                ... on AssignedSingleChoiceAttribute {
                    value {
                        slug
                    }
                }
            }
        }
    }
"""

USER_ASSIGNED_ATTRIBUTE_BY_SLUG_QUERY = """
    query User($id: ID!, $slug: String!) {
        user(id: $id) {
            assignedAttribute(slug: $slug) {
                attribute {
                    slug
                }
                ... on AssignedSingleChoiceAttribute {
                    value {
                        slug
                    }
                }
            }
        }
    }
"""


def test_assigned_attributes_by_staff_with_manage_users(
    staff_api_client,
    permission_manage_users,
    customer_user,
    customer_type_with_attributes,
    loyalty_customer_attribute,
    description_customer_attribute,
    hidden_customer_attribute,
):
    # given
    customer_user.customer_type = customer_type_with_attributes
    customer_user.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="gold")
    AssignedUserAttributeValue.objects.create(user=customer_user, value=value)
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        USER_ASSIGNED_ATTRIBUTES_QUERY,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["user"]["assignedAttributes"]
    slugs = {entry["attribute"]["slug"] for entry in assigned_attributes}
    assert slugs == {
        loyalty_customer_attribute.slug,
        description_customer_attribute.slug,
        hidden_customer_attribute.slug,
    }
    loyalty_entry = next(
        entry
        for entry in assigned_attributes
        if entry["attribute"]["slug"] == loyalty_customer_attribute.slug
    )
    assert loyalty_entry["value"]["slug"] == value.slug


def test_assigned_attributes_by_owner_hides_storefront_invisible(
    user_api_client,
    customer_type_with_attributes,
    loyalty_customer_attribute,
    description_customer_attribute,
    hidden_customer_attribute,
):
    # given
    user = user_api_client.user
    user.customer_type = customer_type_with_attributes
    user.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="silver")
    AssignedUserAttributeValue.objects.create(user=user, value=value)

    # when
    response = user_api_client.post_graphql(ME_ASSIGNED_ATTRIBUTES_QUERY)

    # then
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["me"]["assignedAttributes"]
    slugs = {entry["attribute"]["slug"] for entry in assigned_attributes}
    assert slugs == {
        loyalty_customer_attribute.slug,
        description_customer_attribute.slug,
    }
    loyalty_entry = next(
        entry
        for entry in assigned_attributes
        if entry["attribute"]["slug"] == loyalty_customer_attribute.slug
    )
    assert loyalty_entry["value"]["slug"] == value.slug


def test_assigned_attributes_by_staff_without_manage_users(
    staff_api_client,
    permission_manage_staff,
    admin_user,
):
    # given: a staff user queries another user without MANAGE_USERS
    variables = {"id": graphene.Node.to_global_id("User", admin_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        USER_ASSIGNED_ATTRIBUTES_QUERY,
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_assigned_attributes_fall_back_to_default_customer_type(
    staff_api_client,
    permission_manage_users,
    customer_user,
    default_customer_type,
    segment_customer_attribute,
):
    # given: the user has no customer type assigned yet
    default_customer_type.customer_attributes.add(segment_customer_attribute)
    assert customer_user.customer_type_id is None
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        USER_ASSIGNED_ATTRIBUTES_QUERY,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["user"]["assignedAttributes"]
    slugs = {entry["attribute"]["slug"] for entry in assigned_attributes}
    assert slugs == {segment_customer_attribute.slug}


def test_assigned_attribute_by_slug_by_staff(
    staff_api_client,
    permission_manage_users,
    customer_user,
    customer_type_with_attributes,
    loyalty_customer_attribute,
):
    # given
    customer_user.customer_type = customer_type_with_attributes
    customer_user.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="gold")
    AssignedUserAttributeValue.objects.create(user=customer_user, value=value)
    variables = {
        "id": graphene.Node.to_global_id("User", customer_user.pk),
        "slug": loyalty_customer_attribute.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        USER_ASSIGNED_ATTRIBUTE_BY_SLUG_QUERY,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assigned_attribute = content["data"]["user"]["assignedAttribute"]
    assert assigned_attribute["attribute"]["slug"] == loyalty_customer_attribute.slug
    assert assigned_attribute["value"]["slug"] == value.slug


def test_assigned_attribute_by_slug_hidden_attribute_by_staff(
    staff_api_client,
    permission_manage_users,
    customer_user,
    customer_type_with_attributes,
    hidden_customer_attribute,
):
    # given
    customer_user.customer_type = customer_type_with_attributes
    customer_user.save(update_fields=["customer_type"])
    variables = {
        "id": graphene.Node.to_global_id("User", customer_user.pk),
        "slug": hidden_customer_attribute.slug,
    }

    # when
    response = staff_api_client.post_graphql(
        USER_ASSIGNED_ATTRIBUTE_BY_SLUG_QUERY,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assigned_attribute = content["data"]["user"]["assignedAttribute"]
    assert assigned_attribute["attribute"]["slug"] == hidden_customer_attribute.slug


def test_assigned_attribute_by_slug_hidden_attribute_by_owner(
    user_api_client,
    customer_type_with_attributes,
    hidden_customer_attribute,
):
    # given
    user = user_api_client.user
    user.customer_type = customer_type_with_attributes
    user.save(update_fields=["customer_type"])
    query = """
        query Me($slug: String!) {
            me {
                assignedAttribute(slug: $slug) {
                    attribute {
                        slug
                    }
                }
            }
        }
    """
    variables = {"slug": hidden_customer_attribute.slug}

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["me"]["assignedAttribute"] is None
