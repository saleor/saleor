import graphene
import pytest

from saleor.account.models import Bot
from saleor.graphql.core.enums import PermissionEnum
from tests.api.utils import assert_no_permission, get_graphql_content

BOT_CREATE_MUTATION = """
    mutation BotCreate(
        $name: String, $is_active: Boolean $permissions: [PermissionEnum]){
        botCreate(input:{name: $name, isActive: $is_active, permissions: $permissions})
        {
            authToken
            bot{
                authToken
                permissions{
                    code
                    name
                }
                id
                isActive
                name
            }
            errors{
                field
                message
            }
        }
    }
    """


def test_bot_create_mutation(
    permission_manage_bots, permission_manage_products, staff_api_client, staff_user
):
    query = BOT_CREATE_MUTATION
    staff_user.user_permissions.add(permission_manage_bots)

    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    bot_data = content["data"]["botCreate"]["bot"]
    auth_token = content["data"]["botCreate"]["authToken"]
    bot = Bot.objects.get()
    assert auth_token == bot.auth_token
    assert bot_data["isActive"] == bot.is_active
    assert bot_data["name"] == bot.name
    assert list(bot.permissions.all()) == [permission_manage_products]


def test_bot_create_mutation_no_permissions(
    permission_manage_bots, permission_manage_products, staff_api_client, staff_user
):
    query = BOT_CREATE_MUTATION
    variables = {
        "name": "New integration",
        "is_active": True,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


BOT_UPDATE_MUTATION = """
mutation BotUpdate($id: ID!, $is_active: Boolean, $permissions: [PermissionEnum]){
    botUpdate(id: $id, input:{isActive: $is_active, permissions:$permissions}){
        bot{
            isActive
            id
            authToken
            permissions{
                code
                name
            }
            name
        }
        errors{
            field
            message
        }
    }
}
"""


def test_bot_update_mutation(
    bot,
    permission_manage_bots,
    permission_manage_products,
    permission_manage_users,
    staff_api_client,
    staff_user,
):
    query = BOT_UPDATE_MUTATION
    staff_user.user_permissions.add(permission_manage_bots)
    id = graphene.Node.to_global_id("Bot", bot.id)

    variables = {
        "id": id,
        "is_active": False,
        "permissions": [
            PermissionEnum.MANAGE_PRODUCTS.name,
            PermissionEnum.MANAGE_USERS.name,
        ],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    bot_data = content["data"]["botUpdate"]["bot"]
    bot.refresh_from_db()

    assert bot_data["isActive"] == bot.is_active
    assert bot.is_active is False
    assert bot_data["authToken"] == "*" * 6 + bot.auth_token[-4:]
    assert set(bot.permissions.all()) == {
        permission_manage_products,
        permission_manage_users,
    }


def test_bot_update_no_permission(bot, staff_api_client, staff_user):
    query = BOT_UPDATE_MUTATION
    id = graphene.Node.to_global_id("Bot", bot.id)
    variables = {
        "id": id,
        "is_active": False,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


@pytest.fixture
def query_bots_with_filter():
    query = """
    query ($filter: BotUserInput ){
        bots(first: 5, filter: $filter){
            edges{
                node{
                    id
                    authToken
                    isActive
                    permissions{
                        name
                        code
                    }
                    name
                }
            }
        }
    }
    """
    return query


@pytest.mark.parametrize(
    "bot_filter, count", (({"search": "Sample"}, 1), ({"isActive": False}, 1), ({}, 2))
)
def test_bots_query(
    query_bots_with_filter,
    staff_api_client,
    permission_manage_bots,
    bot,
    bot_filter,
    count,
):
    second_bot = Bot.objects.create(name="Simple bot")
    second_bot.is_active = False
    second_bot.save()

    variables = {"filter": bot_filter}
    response = staff_api_client.post_graphql(
        query_bots_with_filter, variables, permissions=[permission_manage_bots]
    )
    content = get_graphql_content(response)

    bots_data = content["data"]["bots"]["edges"]
    for bot_data in bots_data:
        token = bot_data["node"]["authToken"]
        assert token.startswith("*" * 6)
        assert len(token) == 10
    assert len(bots_data) == count


def test_bots_query_no_permission(
    query_bots_with_filter,
    staff_api_client,
    permission_manage_users,
    permission_manage_staff,
    bot,
):
    variables = {"filter": {}}
    response = staff_api_client.post_graphql(
        query_bots_with_filter, variables, permissions=[]
    )
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        query_bots_with_filter,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


@pytest.fixture
def query_bot():
    query = """
    query ($id: ID! ){
        bot(id: $id){
            id
            authToken
            created
            isActive
            permissions{
                code
                name
            }
            name
        }
    }
    """
    return query


def test_bot_query(
    query_bot, staff_api_client, permission_manage_bots, permission_manage_staff, bot
):
    bot.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("Bot", bot.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        query_bot, variables, permissions=[permission_manage_bots]
    )
    content = get_graphql_content(response)

    bot_data = content["data"]["bot"]
    assert bot_data["authToken"] == "*" * 6 + bot.auth_token[-4:]
    assert bot_data["isActive"] == bot.is_active
    assert bot_data["permissions"] == [
        {"code": "MANAGE_STAFF", "name": "Manage staff."}
    ]


def test_bot_query_no_permission(
    query_bot, staff_api_client, permission_manage_staff, permission_manage_users, bot
):
    bot.permissions.add(permission_manage_staff)

    id = graphene.Node.to_global_id("Bot", bot.id)
    variables = {"id": id}
    response = staff_api_client.post_graphql(query_bot, variables, permissions=[])
    assert_no_permission(response)

    response = staff_api_client.post_graphql(
        query_bot,
        variables,
        permissions=[permission_manage_users, permission_manage_staff],
    )
    assert_no_permission(response)


def test_bot_with_access_to_resources(
    bot_api_client, bot, permission_manage_orders, order_with_lines
):
    query = """
      query {
        orders(first: 5) {
          edges {
            node {
              id
            }
          }
        }
      }
    """
    response = bot_api_client.post_graphql(query)
    assert_no_permission(response)
    bot.permissions.add(permission_manage_orders)
    response = bot_api_client.post_graphql(query)
    get_graphql_content(response)
