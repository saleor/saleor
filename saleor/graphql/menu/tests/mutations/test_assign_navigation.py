import graphene

from ....menu.enums import NavigationType
from ....tests.utils import assert_no_permission, get_graphql_content


def test_assign_menu(
    staff_api_client,
    menu,
    permission_manage_menus,
    permission_manage_settings,
    site_settings,
):
    query = """
    mutation AssignMenu($menu: ID, $navigationType: NavigationType!) {
        assignNavigation(menu: $menu, navigationType: $navigationType) {
            errors {
                field
                message
            }
            menu {
                name
            }
        }
    }
    """

    # test mutations fails without proper permissions
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)
    variables = {"menu": menu_id, "navigationType": NavigationType.MAIN.name}
    response = staff_api_client.post_graphql(query, variables)
    assert_no_permission(response)

    staff_api_client.user.user_permissions.add(permission_manage_menus)
    staff_api_client.user.user_permissions.add(permission_manage_settings)

    # test assigning main menu
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["assignNavigation"]["menu"]["name"] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.top_menu.name == menu.name

    # test assigning secondary menu
    variables = {"menu": menu_id, "navigationType": NavigationType.SECONDARY.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["assignNavigation"]["menu"]["name"] == menu.name
    site_settings.refresh_from_db()
    assert site_settings.bottom_menu.name == menu.name

    # test unasigning menu
    variables = {"id": None, "navigationType": NavigationType.MAIN.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not content["data"]["assignNavigation"]["menu"]
    site_settings.refresh_from_db()
    assert site_settings.top_menu is None
