import graphene

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
    assert set(bot.permissions.all()) == set(
        [permission_manage_products, permission_manage_users]
    )


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


# def test_bots_query()
# {
#   bots(first:5){
#     edges{
#       node{
#         id
#         authToken
#         isActive
#         permissions{
#           name
#           code
#         }
#         name
#       }
#     }
#   }
# }


# {
#   bot(id:"Qm90OjE="){
#     id
#     authToken
#     created
#     isActive
#     permissions{
#       code
#       name
#     }
#     name
#   }
# }
