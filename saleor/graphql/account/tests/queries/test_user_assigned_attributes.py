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
    customer_user.customer_type = None
    customer_user.save(update_fields=["customer_type"])
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


def test_assigned_attributes_kept_after_switch_to_type_sharing_the_attribute(
    staff_api_client,
    permission_manage_users,
    customer_user,
    customer_type,
    default_customer_type,
    loyalty_customer_attribute,
):
    # given: the attribute belongs to two customer types and the value was
    # assigned while the user belonged to the first one
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    default_customer_type.customer_attributes.add(loyalty_customer_attribute)
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    value = loyalty_customer_attribute.values.get(slug="gold")
    AssignedUserAttributeValue.objects.create(user=customer_user, value=value)
    user_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": user_id}

    response = staff_api_client.post_graphql(
        USER_ASSIGNED_ATTRIBUTES_QUERY,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["user"]["assignedAttributes"]
    assert len(assigned_attributes) == 1
    assert (
        assigned_attributes[0]["attribute"]["slug"] == loyalty_customer_attribute.slug
    )
    assert assigned_attributes[0]["value"]["slug"] == value.slug

    # when: the user switches to the other type sharing the attribute
    mutation = """
        mutation CustomerUpdate($id: ID!, $input: CustomerInput!) {
            customerUpdate(id: $id, input: $input) {
                user {
                    customerType {
                        id
                    }
                }
                errors {
                    field
                    code
                    message
                }
            }
        }
    """
    default_customer_type_id = graphene.Node.to_global_id(
        "CustomerType", default_customer_type.pk
    )
    mutation_variables = {
        "id": user_id,
        "input": {"customerType": default_customer_type_id},
    }
    response = staff_api_client.post_graphql(mutation, mutation_variables)
    content = get_graphql_content(response)
    data = content["data"]["customerUpdate"]
    assert data["errors"] == []
    assert data["user"]["customerType"]["id"] == default_customer_type_id

    # then: the value stays visible because the new type also has the attribute
    response = staff_api_client.post_graphql(USER_ASSIGNED_ATTRIBUTES_QUERY, variables)
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["user"]["assignedAttributes"]
    assert len(assigned_attributes) == 1
    assert (
        assigned_attributes[0]["attribute"]["slug"] == loyalty_customer_attribute.slug
    )
    assert assigned_attributes[0]["value"]["slug"] == value.slug


USER_ASSIGNED_MULTISELECT_VALUE_LIMIT_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            assignedAttributes {
                attribute {
                    slug
                }
                ... on AssignedMultiChoiceAttribute {
                    value(limit: 2) {
                        slug
                    }
                }
            }
        }
    }
"""


def test_assigned_multiselect_value_limit_truncates(
    staff_api_client,
    permission_manage_users,
    customer_user,
    customer_type,
    interests_customer_attribute,
):
    # given: three values assigned, a limit of two
    customer_type.customer_attributes.add(interests_customer_attribute)
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    sports = interests_customer_attribute.values.get(slug="sports")
    music = interests_customer_attribute.values.get(slug="music")
    travel = interests_customer_attribute.values.get(slug="travel")
    for value in [sports, music, travel]:
        AssignedUserAttributeValue.objects.create(user=customer_user, value=value)
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        USER_ASSIGNED_MULTISELECT_VALUE_LIMIT_QUERY,
        variables,
        permissions=[permission_manage_users],
    )

    # then: only the first two values in assignment order are returned
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["user"]["assignedAttributes"]
    assert assigned_attributes == [
        {
            "attribute": {"slug": interests_customer_attribute.slug},
            "value": [{"slug": sports.slug}, {"slug": music.slug}],
        }
    ]


def test_assigned_attributes_limit_caps_attribute_count(
    staff_api_client,
    permission_manage_users,
    customer_user,
    customer_type,
    loyalty_customer_attribute,
    description_customer_attribute,
    hidden_customer_attribute,
):
    # given: the customer type holds three attributes, a limit of one.
    # Separate add() calls per attribute - a single call iterates an
    # unordered set of ids, making the insertion (and thus fallback pk)
    # ordering nondeterministic.
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    customer_type.customer_attributes.add(description_customer_attribute)
    customer_type.customer_attributes.add(hidden_customer_attribute)
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    query = """
        query User($id: ID!) {
            user(id: $id) {
                assignedAttributes(limit: 1) {
                    attribute {
                        slug
                    }
                }
            }
        }
    """
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_users],
    )

    # then: only the first attribute of the customer type is returned
    content = get_graphql_content(response)
    assigned_attributes = content["data"]["user"]["assignedAttributes"]
    assert assigned_attributes == [
        {"attribute": {"slug": loyalty_customer_attribute.slug}}
    ]


def test_assigned_multiselect_value_limit_partitions_per_user(
    staff_api_client,
    permission_manage_users,
    customer_users,
    customer_type,
    interests_customer_attribute,
):
    # given: two users with the same values assigned in opposite orders
    customer_type.customer_attributes.add(interests_customer_attribute)
    first_user, second_user = customer_users[:2]
    for user in [first_user, second_user]:
        user.customer_type = customer_type
        user.save(update_fields=["customer_type"])
    sports = interests_customer_attribute.values.get(slug="sports")
    music = interests_customer_attribute.values.get(slug="music")
    travel = interests_customer_attribute.values.get(slug="travel")
    for value in [sports, music, travel]:
        AssignedUserAttributeValue.objects.create(user=first_user, value=value)
    for value in [travel, music, sports]:
        AssignedUserAttributeValue.objects.create(user=second_user, value=value)
    query = """
        query Users($firstId: ID!, $secondId: ID!) {
            firstUser: user(id: $firstId) {
                assignedAttributes {
                    ... on AssignedMultiChoiceAttribute {
                        value(limit: 2) {
                            slug
                        }
                    }
                }
            }
            secondUser: user(id: $secondId) {
                assignedAttributes {
                    ... on AssignedMultiChoiceAttribute {
                        value(limit: 2) {
                            slug
                        }
                    }
                }
            }
        }
    """
    variables = {
        "firstId": graphene.Node.to_global_id("User", first_user.pk),
        "secondId": graphene.Node.to_global_id("User", second_user.pk),
    }

    # when: both users are resolved in a single request
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_users],
    )

    # then: each user gets their own first two values in their own order
    content = get_graphql_content(response)
    first_values = content["data"]["firstUser"]["assignedAttributes"][0]["value"]
    second_values = content["data"]["secondUser"]["assignedAttributes"][0]["value"]
    assert first_values == [{"slug": sports.slug}, {"slug": music.slug}]
    assert second_values == [{"slug": travel.slug}, {"slug": music.slug}]


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
