from ......account.error_codes import CustomerTagErrorCode
from ......account.models import CustomerTag
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TAG_CREATE_MUTATION = """
    mutation CustomerTagCreate($input: CustomerTagCreateInput!) {
        customerTagCreate(input: $input) {
            customerTag {
                id
                name
                slug
                description
                isPublic
                memberCount
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_customer_tag_create(staff_api_client, permission_manage_customer_tags):
    # given
    name = "VIP"
    variables = {
        "input": {
            "name": name,
            "isPublic": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then the response and the persisted row both reflect the input
    content = get_graphql_content(response)
    data = content["data"]["customerTagCreate"]
    assert data["errors"] == []
    assert data["customerTag"]["name"] == name
    assert data["customerTag"]["slug"] == "vip"
    assert data["customerTag"]["isPublic"] is True
    assert data["customerTag"]["memberCount"] == 0
    tag = CustomerTag.objects.get(slug="vip")
    assert tag.name == name
    # grounded in the real DB value written through the mutation
    assert tag.is_public is True


def test_customer_tag_create_defaults_to_not_public(
    staff_api_client, permission_manage_customer_tags
):
    # given isPublic is omitted
    variables = {"input": {"name": "Wholesale"}}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then it is private by default, in both the response and the DB
    content = get_graphql_content(response)
    data = content["data"]["customerTagCreate"]
    assert data["errors"] == []
    assert data["customerTag"]["isPublic"] is False
    assert CustomerTag.objects.get(slug="wholesale").is_public is False


def test_customer_tag_create_with_explicit_slug(
    staff_api_client, permission_manage_customer_tags
):
    # given
    slug = "vip-tier"
    variables = {"input": {"name": "VIP", "slug": slug}}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagCreate"]
    assert data["errors"] == []
    assert data["customerTag"]["slug"] == slug


def test_customer_tag_create_duplicated_slug(
    staff_api_client, permission_manage_customer_tags, customer_tag
):
    # given
    variables = {"input": {"name": "Another", "slug": customer_tag.slug}}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_CREATE_MUTATION,
        variables,
        permissions=[permission_manage_customer_tags],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTagCreate"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "slug"
    assert data["errors"][0]["code"] == CustomerTagErrorCode.UNIQUE.name
    assert data["customerTag"] is None


def test_customer_tag_create_no_permission(staff_api_client):
    # given
    variables = {"input": {"name": "VIP"}}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TAG_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_customer_tag_create_assign_permission_is_insufficient(
    staff_api_client, permission_assign_customer_tags
):
    # given
    variables = {"input": {"name": "VIP"}}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TAG_CREATE_MUTATION,
        variables,
        permissions=[permission_assign_customer_tags],
    )

    # then
    assert_no_permission(response)
