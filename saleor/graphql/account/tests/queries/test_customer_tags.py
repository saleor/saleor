import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from ...sorters import CustomerTagSortField

CUSTOMER_TAGS_QUERY = """
    query CustomerTags {
        customerTags(first: 10) {
            edges {
                node {
                    id
                    name
                    slug
                    memberCount
                }
            }
        }
    }
"""

CUSTOMER_TAGS_SORTED_QUERY = """
    query CustomerTags($sortBy: CustomerTagSortingInput) {
        customerTags(first: 10, sortBy: $sortBy) {
            edges {
                node {
                    slug
                    memberCount
                }
            }
        }
    }
"""

CUSTOMER_TAG_QUERY = """
    query CustomerTag($id: ID, $slug: String) {
        customerTag(id: $id, slug: $slug) {
            id
            name
            slug
        }
    }
"""


def test_query_customer_tags(
    staff_api_client, permission_manage_customer_tags, customer_tags
):
    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAGS_QUERY, permissions=[permission_manage_customer_tags]
    )

    # then
    content = get_graphql_content(response)
    edges = content["data"]["customerTags"]["edges"]
    returned_slugs = {edge["node"]["slug"] for edge in edges}
    assert returned_slugs == {tag.slug for tag in customer_tags}


def test_query_customer_tags_no_permission(api_client, customer_tags):
    # when
    response = api_client.post_graphql(CUSTOMER_TAGS_QUERY)

    # then
    assert_no_permission(response)


def test_query_customer_tag_member_count_is_computed(
    staff_api_client, permission_manage_customer_tags, customer_tag, customer_users
):
    # given users really assigned to the tag in the DB
    customer_tag.users.add(*customer_users)

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAGS_QUERY, permissions=[permission_manage_customer_tags]
    )

    # then memberCount reflects the actual number of assigned users
    content = get_graphql_content(response)
    counts = {
        edge["node"]["slug"]: edge["node"]["memberCount"]
        for edge in content["data"]["customerTags"]["edges"]
    }
    assert counts[customer_tag.slug] == len(customer_users)


def test_query_customer_tags_sorted_by_member_count(
    staff_api_client, permission_manage_customer_tags, customer_tags, customer_users
):
    # given three tags with distinct member counts (employee=0, vip=1, wholesale=2)
    vip, wholesale, employee = customer_tags
    vip.users.add(customer_users[0])
    wholesale.users.add(*customer_users)
    variables = {
        "sortBy": {
            "field": CustomerTagSortField.MEMBER_COUNT.name,
            "direction": "ASC",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAGS_SORTED_QUERY,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then they come back ordered by ascending member count
    content = get_graphql_content(response)
    edges = content["data"]["customerTags"]["edges"]
    slugs_in_order = [edge["node"]["slug"] for edge in edges]
    counts_in_order = [edge["node"]["memberCount"] for edge in edges]
    assert slugs_in_order == [employee.slug, vip.slug, wholesale.slug]
    assert counts_in_order == [0, 1, len(customer_users)]


def test_query_customer_tag_by_slug(
    staff_api_client, permission_manage_customer_tags, customer_tag
):
    # given
    variables = {"slug": customer_tag.slug}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_QUERY,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTag"]
    assert data["slug"] == customer_tag.slug
    assert data["name"] == customer_tag.name


def test_query_customer_tag_by_id(
    staff_api_client, permission_manage_customer_tags, customer_tag
):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerTag", customer_tag.pk)}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_QUERY,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerTag"]["slug"] == customer_tag.slug


CUSTOMER_TAG_USERS_QUERY = """
    query CustomerTag($slug: String, $first: Int) {
        customerTag(slug: $slug) {
            slug
            users(first: $first) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
"""


def test_query_customer_tag_users_connection(
    staff_api_client, permission_manage_customer_tags, customer_tag, customer_users
):
    # given users assigned to the tag
    customer_tag.users.add(*customer_users)
    variables = {"slug": customer_tag.slug, "first": 10}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_USERS_QUERY,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then the users are returned as a paginated connection
    content = get_graphql_content(response)
    data = content["data"]["customerTag"]["users"]
    assert data["totalCount"] == len(customer_users)
    returned_ids = {edge["node"]["id"] for edge in data["edges"]}
    expected_ids = {
        graphene.Node.to_global_id("User", user.pk) for user in customer_users
    }
    assert returned_ids == expected_ids


def test_query_customer_tag_users_no_permission(
    user_api_client, customer_tag, customer_users
):
    # given
    customer_tag.users.add(*customer_users)
    variables = {"slug": customer_tag.slug, "first": 10}

    # when
    response = user_api_client.post_graphql(CUSTOMER_TAG_USERS_QUERY, variables)

    # then the whole customerTag query requires tag-management permission
    assert_no_permission(response)


USER_TAGS_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            tags {
                slug
            }
        }
    }
"""

ME_TAGS_QUERY = """
    query Me {
        me {
            tags {
                slug
            }
        }
    }
"""


CUSTOMER_TAG_CREATE_MUTATION = """
    mutation CustomerTagCreate($input: CustomerTagCreateInput!) {
        customerTagCreate(input: $input) {
            customerTag {
                id
            }
            errors {
                field
                code
            }
        }
    }
"""

CUSTOMER_TAG_ASSIGN_MUTATION = """
    mutation Assign($userIds: [ID!]!, $tagIds: [ID!]!) {
        customerTagAssign(userIds: $userIds, tagIds: $tagIds) {
            customerTags {
                id
            }
            errors {
                field
                code
            }
        }
    }
"""


def _create_tag_via_api(staff_api_client, *, name, slug, is_public):
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_CREATE_MUTATION,
        {"input": {"name": name, "slug": slug, "isPublic": is_public}},
    )
    content = get_graphql_content(response)
    data = content["data"]["customerTagCreate"]
    assert data["errors"] == []
    return data["customerTag"]["id"]


def _assign_tags_via_api(staff_api_client, user, tag_ids):
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_ASSIGN_MUTATION,
        {
            "userIds": [graphene.Node.to_global_id("User", user.pk)],
            "tagIds": tag_ids,
        },
    )
    content = get_graphql_content(response)
    assert content["data"]["customerTagAssign"]["errors"] == []


def test_staff_sees_all_user_tags(
    staff_api_client,
    permission_manage_customer_tags,
    permission_assign_customer_tags,
    permission_manage_users,
    customer_user,
):
    # given a public and a private tag created + assigned through the real API
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_tags,
        permission_assign_customer_tags,
        permission_manage_users,
    )
    public_id = _create_tag_via_api(
        staff_api_client, name="VIP", slug="vip", is_public=True
    )
    private_id = _create_tag_via_api(
        staff_api_client, name="Wholesale", slug="wholesale", is_public=False
    )
    _assign_tags_via_api(staff_api_client, customer_user, [public_id, private_id])
    variables = {"id": graphene.Node.to_global_id("User", customer_user.pk)}

    # when
    response = staff_api_client.post_graphql(USER_TAGS_QUERY, variables)

    # then staff sees every assigned tag, regardless of visibility
    content = get_graphql_content(response)
    slugs = {tag["slug"] for tag in content["data"]["user"]["tags"]}
    assert slugs == {"vip", "wholesale"}


def test_me_tags_returns_only_public_tags(
    staff_api_client,
    user_api_client,
    permission_manage_customer_tags,
    permission_assign_customer_tags,
    customer_user,
):
    # given a public and a private tag created + assigned through the real API
    # (this exercises the real write path so a storage/visibility mismatch fails)
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_tags, permission_assign_customer_tags
    )
    public_id = _create_tag_via_api(
        staff_api_client, name="VIP", slug="vip", is_public=True
    )
    private_id = _create_tag_via_api(
        staff_api_client, name="Wholesale", slug="wholesale", is_public=False
    )
    _assign_tags_via_api(staff_api_client, customer_user, [public_id, private_id])

    # when the customer queries their own tags on the storefront
    response = user_api_client.post_graphql(ME_TAGS_QUERY)

    # then only the public tag is visible
    content = get_graphql_content(response)
    slugs = {tag["slug"] for tag in content["data"]["me"]["tags"]}
    assert slugs == {"vip"}
