"""POC: READ_USERS / READ_STAFF permission model (account domain).

Acceptance scenarios from .context/read-permission-poc-scenarios.md.
Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity      - READ_X sees the same reads as MANAGE_X
  B. No write leak - READ_X is rejected by MANAGE_X mutations
  C. Regression  - MANAGE_X behavior unchanged; no-perms still denied
  D. App carve-out - READ_STAFF is app-grantable; MANAGE_STAFF is not
  E. Metadata    - READ_X unlocks private metadata reads (dynamic perm resolution)
"""

from ...core.utils import to_global_id_or_none
from ...tests.utils import assert_no_permission, get_graphql_content

CUSTOMERS_QUERY = """
    query {
        customers(first: 10) {
            edges { node { id email } }
        }
    }
"""

STAFF_USERS_QUERY = """
    query {
        staffUsers(first: 10) {
            edges { node { id email } }
        }
    }
"""

PERMISSION_GROUPS_QUERY = """
    query {
        permissionGroups(first: 10) {
            edges { node { id name } }
        }
    }
"""

USER_QUERY = """
    query ($id: ID!) {
        user(id: $id) { id email }
    }
"""

USER_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        user(id: $id) {
            id
            privateMetadata { key value }
        }
    }
"""

CUSTOMER_UPDATE_MUTATION = """
    mutation ($id: ID!) {
        customerUpdate(id: $id, input: {firstName: "Changed"}) {
            user { id }
            errors { field code }
        }
    }
"""

PERMISSION_GROUP_CREATE_MUTATION = """
    mutation {
        permissionGroupCreate(input: {name: "New group"}) {
            group { id }
            errors { field code }
        }
    }
"""


# --------------------------------------------------------------------------- #
# A. Parity - READ_X sees the same reads as MANAGE_X
# --------------------------------------------------------------------------- #


def test_read_users_grants_customers_list(
    staff_api_client, customer_user, permission_read_users
):
    # given a staff user holding only READ_USERS
    staff_api_client.user.user_permissions.add(permission_read_users)

    # when querying the customers list
    response = staff_api_client.post_graphql(CUSTOMERS_QUERY)

    # then the customer row is returned (field opens AND row is visible)
    content = get_graphql_content(response)
    emails = {edge["node"]["email"] for edge in content["data"]["customers"]["edges"]}
    assert customer_user.email in emails


def test_read_staff_grants_staff_users_list(staff_api_client, permission_read_staff):
    # given a staff user holding only READ_STAFF
    staff_api_client.user.user_permissions.add(permission_read_staff)

    # when querying the staff users list
    response = staff_api_client.post_graphql(STAFF_USERS_QUERY)

    # then the requesting staff user is returned
    content = get_graphql_content(response)
    emails = {edge["node"]["email"] for edge in content["data"]["staffUsers"]["edges"]}
    assert staff_api_client.user.email in emails


def test_read_staff_grants_permission_groups(
    staff_api_client, permission_group_manage_staff, permission_read_staff
):
    # given a staff user holding only READ_STAFF and an existing group
    staff_api_client.user.user_permissions.add(permission_read_staff)

    # when querying permission groups
    response = staff_api_client.post_graphql(PERMISSION_GROUPS_QUERY)

    # then the group is returned
    content = get_graphql_content(response)
    names = {
        edge["node"]["name"] for edge in content["data"]["permissionGroups"]["edges"]
    }
    assert permission_group_manage_staff.name in names


def test_read_users_grants_user_lookup_for_customer(
    staff_api_client, customer_user, permission_read_users
):
    # given a staff user holding only READ_USERS
    staff_api_client.user.user_permissions.add(permission_read_users)
    # when looking up a customer by id
    variables = {"id": to_global_id_or_none(customer_user)}
    response = staff_api_client.post_graphql(USER_QUERY, variables)

    # then the customer is returned
    content = get_graphql_content(response)
    assert content["data"]["user"]["email"] == customer_user.email


def test_read_staff_grants_user_lookup_for_staff(
    staff_api_client, staff_user, permission_read_staff
):
    # given a staff user holding only READ_STAFF
    staff_api_client.user.user_permissions.add(permission_read_staff)
    # when looking up a staff user by id
    variables = {"id": to_global_id_or_none(staff_user)}
    response = staff_api_client.post_graphql(USER_QUERY, variables)

    # then the staff user is returned
    content = get_graphql_content(response)
    assert content["data"]["user"]["email"] == staff_user.email


# --------------------------------------------------------------------------- #
# B. No write leak - READ_X is rejected by MANAGE_X mutations
# --------------------------------------------------------------------------- #


def test_read_users_cannot_update_customer(
    staff_api_client, customer_user, permission_read_users
):
    # given a staff user holding only READ_USERS
    staff_api_client.user.user_permissions.add(permission_read_users)
    # when attempting a MANAGE_USERS mutation
    variables = {"id": to_global_id_or_none(customer_user)}
    response = staff_api_client.post_graphql(CUSTOMER_UPDATE_MUTATION, variables)

    # then it is denied and the record is unchanged
    assert_no_permission(response)
    customer_user.refresh_from_db()
    assert customer_user.first_name != "Changed"


def test_read_staff_cannot_create_permission_group(
    staff_api_client, permission_read_staff
):
    # given a staff user holding only READ_STAFF
    staff_api_client.user.user_permissions.add(permission_read_staff)

    # when attempting a MANAGE_STAFF mutation
    response = staff_api_client.post_graphql(PERMISSION_GROUP_CREATE_MUTATION)

    # then it is denied
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_X unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_users_still_reads_customers(
    staff_api_client, customer_user, permission_manage_users
):
    # given a staff user holding MANAGE_USERS (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_users)

    # when querying the customers list
    response = staff_api_client.post_graphql(CUSTOMERS_QUERY)

    # then the customer is returned (no regression)
    content = get_graphql_content(response)
    emails = {edge["node"]["email"] for edge in content["data"]["customers"]["edges"]}
    assert customer_user.email in emails


def test_no_perms_staff_cannot_read_customers(staff_api_client, customer_user):
    # given a staff user with no relevant permissions
    # when querying the customers list
    response = staff_api_client.post_graphql(CUSTOMERS_QUERY)

    # then access is denied - adding READ twins did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# D. App carve-out - READ_STAFF is app-grantable; MANAGE_STAFF is not
# --------------------------------------------------------------------------- #


def test_app_with_read_staff_can_read_staff_users(
    app_api_client, staff_user, permission_read_staff
):
    # given an app holding READ_STAFF
    app_api_client.app.permissions.add(permission_read_staff)

    # when querying staff users
    response = app_api_client.post_graphql(STAFF_USERS_QUERY)

    # then data is returned - the app carve-out does not block READ_STAFF
    content = get_graphql_content(response)
    emails = {edge["node"]["email"] for edge in content["data"]["staffUsers"]["edges"]}
    assert staff_user.email in emails


def test_app_with_manage_staff_is_still_blocked(
    app_api_client, permission_manage_staff
):
    # given an app assigned MANAGE_STAFF
    app_api_client.app.permissions.add(permission_manage_staff)

    # when attempting a MANAGE_STAFF mutation
    response = app_api_client.post_graphql(PERMISSION_GROUP_CREATE_MUTATION)

    # then it is denied - MANAGE_STAFF remains unreachable for apps
    assert_no_permission(response)


def test_app_with_read_users_can_read_customers(
    app_api_client, customer_user, permission_read_users
):
    # given an app holding READ_USERS
    app_api_client.app.permissions.add(permission_read_users)

    # when querying the customers list
    response = app_api_client.post_graphql(CUSTOMERS_QUERY)

    # then customers are returned (apps are a primary target audience)
    content = get_graphql_content(response)
    emails = {edge["node"]["email"] for edge in content["data"]["customers"]["edges"]}
    assert customer_user.email in emails


# --------------------------------------------------------------------------- #
# E. Metadata - READ_X unlocks private metadata reads (dynamic perm resolution)
# --------------------------------------------------------------------------- #


def test_read_users_reads_customer_private_metadata(
    staff_api_client, customer_user, permission_read_users
):
    # given a customer with private metadata and a READ_USERS-only staff user
    customer_user.store_value_in_private_metadata({"secret": "value"})
    customer_user.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_users)
    # when reading the customer's private metadata
    variables = {"id": to_global_id_or_none(customer_user)}
    response = staff_api_client.post_graphql(USER_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["user"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


def test_read_staff_reads_staff_private_metadata(
    staff_api_client, staff_user, permission_read_staff
):
    # given a staff user with private metadata and a READ_STAFF-only requestor
    staff_user.store_value_in_private_metadata({"secret": "value"})
    staff_user.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_staff)
    # when reading the staff user's private metadata
    variables = {"id": to_global_id_or_none(staff_user)}
    response = staff_api_client.post_graphql(USER_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["user"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


def test_read_users_cannot_read_staff_private_metadata(
    staff_api_client, staff_user, permission_read_users, permission_manage_users
):
    # given a staff user with private metadata
    secret = {"secret": "value"}
    staff_user.store_value_in_private_metadata(secret)
    staff_user.save(update_fields=["private_metadata"])
    variables = {"id": to_global_id_or_none(staff_user)}

    # when a MANAGE_USERS-only principal (customer scope) looks up the staff target
    staff_api_client.user.user_permissions.add(permission_manage_users)
    manage_response = staff_api_client.post_graphql(USER_PRIVATE_META_QUERY, variables)
    manage_content = get_graphql_content(manage_response)

    # then the staff user is invisible in customer scope, so no metadata leaks
    assert manage_content["data"]["user"] is None

    # and a READ_USERS-only principal behaves byte-identically (parity, no leak)
    staff_api_client.user.user_permissions.set([permission_read_users])
    read_response = staff_api_client.post_graphql(USER_PRIVATE_META_QUERY, variables)
    read_content = get_graphql_content(read_response)
    assert read_content["data"]["user"] is None
    assert read_content["data"] == manage_content["data"]
