import graphene

from .....menu.models import Menu
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_MENU = """
    query ($id: ID, $name: String, $slug: String){
        menu(
            id: $id,
            name: $name,
            slug: $slug
        ) {
            id
            name
            slug
        }
    }
    """


def test_menu_query_by_id(
    user_api_client,
    menu,
):
    # given
    variables = {"id": graphene.Node.to_global_id("Menu", menu.pk)}

    # when
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)

    # then
    content = get_graphql_content(response)
    menu_data = content["data"]["menu"]
    assert menu_data is not None
    assert menu_data["name"] == menu.name


def test_staff_query_menu_by_invalid_id(staff_api_client, menu):
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(QUERY_MENU, variables)

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Menu."
    assert content["data"]["menu"] is None


def test_staff_query_menu_with_invalid_object_type(staff_api_client, menu):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", menu.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_MENU, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["menu"] is None


def test_menu_query_by_name(
    user_api_client,
    menu,
):
    # given
    variables = {"name": menu.name}

    # when
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)

    # then
    content = get_graphql_content(response)
    menu_data = content["data"]["menu"]
    assert menu_data is not None
    assert menu_data["name"] == menu.name


def test_menu_query_by_slug(user_api_client):
    # given
    menu = Menu.objects.create(name="test_menu_name", slug="test_menu_name")
    variables = {"slug": menu.slug}

    # when
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)

    # then
    content = get_graphql_content(response)
    menu_data = content["data"]["menu"]
    assert menu_data is not None
    assert menu_data["name"] == menu.name
    assert menu_data["slug"] == menu.slug


def test_menu_query_error_when_id_and_name_provided(
    user_api_client,
    menu,
    graphql_log_handler,
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu.pk),
        "name": menu.name,
    }

    # when
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)

    # then
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_menu_query_error_when_no_param(
    user_api_client,
    menu,
    graphql_log_handler,
):
    # given
    variables = {}

    # when
    response = user_api_client.post_graphql(QUERY_MENU, variables=variables)

    # then
    assert graphql_log_handler.messages == [
        "saleor.graphql.errors.handled[INFO].GraphQLError"
    ]
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1


def test_menu_query(user_api_client, menu):
    query = """
    query menu($id: ID, $menu_name: String){
        menu(id: $id, name: $menu_name) {
            name
        }
    }
    """

    # test query by name
    variables = {"menu_name": menu.name}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["menu"]["name"] == menu.name

    # test query by id
    menu_id = graphene.Node.to_global_id("Menu", menu.id)
    variables = {"id": menu_id}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["menu"]["name"] == menu.name

    # test query by invalid name returns null
    variables = {"menu_name": "not-a-menu"}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["menu"]


def test_menu_items_query(
    user_api_client, menu_with_items, published_collection, channel_USD, category
):
    # given
    query = """
    fragment SecondaryMenuSubItem on MenuItem {
        id
        name
        category {
            id
            name
        }
        url
        collection {
            id
            name
        }
        page {
            slug
        }
    }
    query menuitem($id: ID!, $channel: String) {
        menu(id: $id, channel: $channel) {
            items {
                ...SecondaryMenuSubItem
                children {
                ...SecondaryMenuSubItem
                }
            }
        }
    }
    """
    variables = {
        "id": graphene.Node.to_global_id("Menu", menu_with_items.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)

    items = content["data"]["menu"]["items"]
    assert not items[0]["category"]
    assert not items[0]["collection"]
    assert items[1]["children"][0]["category"]["name"] == category.name
    assert items[1]["children"][1]["collection"]["name"] == published_collection.name
