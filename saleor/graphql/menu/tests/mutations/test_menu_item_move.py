import json
from unittest import mock

import graphene

from .....menu.models import Menu, MenuItem
from ....tests.utils import get_graphql_content

QUERY_REORDER_MENU = """
mutation menuItemMove($menu: ID!, $moves: [MenuItemMoveInput!]!) {
  menuItemMove(menu: $menu, moves: $moves) {
    errors {
      field
      message
    }

    menu {
      id
      items {
        id
        parent {
          id
        }
        children {
          id
          parent {
            id
          }
          children {
            id
          }
        }
      }
    }
  }
}
"""


def test_menu_reorder(staff_api_client, permission_manage_menus, menu_item_list):
    # given
    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 2},
        {"itemId": items_global_ids[1], "parentId": None, "sortOrder": None},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -2},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[2], "parent": None, "children": []},
            {"id": items_global_ids[1], "parent": None, "children": []},
            {"id": items_global_ids[0], "parent": None, "children": []},
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the order is right
    assert menu_data == expected_data


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_menu_reorder_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_menus,
    menu_item_list,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 2},
        {"itemId": items_global_ids[1], "parentId": None, "sortOrder": None},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -2},
    ]

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    assert response["menu"]
    assert not response["errors"]
    assert mocked_webhook_trigger.call_count == 2


def test_menu_reorder_move_the_same_item_multiple_times(
    staff_api_client, permission_manage_menus, menu_item_list
):
    # given
    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": None, "sortOrder": 1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -1},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[2], "parent": None, "children": []},
            {"id": items_global_ids[1], "parent": None, "children": []},
            {"id": items_global_ids[0], "parent": None, "children": []},
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the order is right
    assert menu_data == expected_data


def test_menu_reorder_move_without_effect(
    staff_api_client, permission_manage_menus, menu_item_list
):
    # given
    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    assert len(menu_item_list) == 3

    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": 3},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": -1},
    ]

    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": items_global_ids[0], "parent": None, "children": []},
            {"id": items_global_ids[2], "parent": None, "children": []},
            {"id": items_global_ids[1], "parent": None, "children": []},
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the order is right
    assert menu_data == expected_data


def test_menu_reorder_assign_parent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Assign a menu item as parent of given menu items. Ensure the menu items
    are properly pushed at the bottom of the item's children.
    """
    # given
    menu_item_list = list(menu_item_list)
    assert len(menu_item_list) == 3

    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[1].menu_id)

    root = menu_item_list[0]
    item0 = MenuItem.objects.create(menu=root.menu, parent=root, name="Default Link")
    menu_item_list.insert(0, item0)

    parent_global_id = graphene.Node.to_global_id("MenuItem", root.pk)
    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[0], "parentId": parent_global_id, "sortOrder": 3},
        {
            "itemId": items_global_ids[2],
            "parentId": parent_global_id,
            "sortOrder": None,
        },
        {"itemId": items_global_ids[3], "parentId": parent_global_id, "sortOrder": -3},
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[1],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[3],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
                    {
                        "id": items_global_ids[0],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
                    {
                        "id": items_global_ids[2],
                        "parent": {"id": parent_global_id},
                        "children": [],
                    },
                ],
            }
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the parent and sort orders were assigned correctly
    assert menu_data == expected_data


def test_menu_reorder_assign_and_unassign_parent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Assign a menu item as parent of given menu items. Ensure the menu items
    are properly pushed at the bottom of the item's children.
    """

    # given
    menu_item_list = list(menu_item_list)
    assert len(menu_item_list) == 3

    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[1].menu_id)

    root = menu_item_list[0]

    item1 = menu_item_list[1]
    item1.parent = root
    item1.save()

    item2 = menu_item_list[2]

    item2_child = MenuItem.objects.create(menu=root.menu, parent=item2, name="Child")

    root_id = graphene.Node.to_global_id("MenuItem", root.pk)
    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[2], "parentId": root_id, "sortOrder": 1},
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": 1},
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[0],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[1],
                        "parent": {"id": root_id},
                        "children": [],
                    },
                ],
            },
            {
                "id": items_global_ids[2],
                "parent": None,
                "children": [
                    {
                        "id": graphene.Node.to_global_id("MenuItem", item2_child.pk),
                        "parent": {"id": items_global_ids[2]},
                        "children": [],
                    },
                ],
            },
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the parent and sort orders were assigned correctly
    assert menu_data == expected_data


def test_menu_reorder_unassign_and_assign_parent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Assign a menu item as parent of given menu items. Ensure the menu items
    are properly pushed at the bottom of the item's children.
    """

    # given
    menu_item_list = list(menu_item_list)
    assert len(menu_item_list) == 3

    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[1].menu_id)

    root = menu_item_list[0]

    item1 = menu_item_list[1]
    item1.parent = root
    item1.save()

    item2 = menu_item_list[2]
    item2.parent = root
    item2.save()

    item2_child = MenuItem.objects.create(menu=root.menu, parent=item2, name="Child")

    root_id = graphene.Node.to_global_id("MenuItem", root.pk)
    items_global_ids = [
        graphene.Node.to_global_id("MenuItem", item.pk) for item in menu_item_list
    ]

    moves_input = [
        {"itemId": items_global_ids[2], "parentId": None, "sortOrder": 1},
        {"itemId": items_global_ids[2], "parentId": root_id, "sortOrder": -1},
    ]

    expected_data = {
        "id": menu_id,
        "items": [
            {
                "id": items_global_ids[0],
                "parent": None,
                "children": [
                    {
                        "id": items_global_ids[2],
                        "parent": {"id": root_id},
                        "children": [
                            {
                                "id": graphene.Node.to_global_id(
                                    "MenuItem", item2_child.pk
                                ),
                            },
                        ],
                    },
                    {
                        "id": items_global_ids[1],
                        "parent": {"id": root_id},
                        "children": [],
                    },
                ],
            },
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the parent and sort orders were assigned correctly
    assert menu_data == expected_data


def test_menu_reorder_assign_parent_to_top_level(
    staff_api_client, permission_manage_menus, menu_item_list
):
    """Set the parent of an item to None, to put it as to the root level."""

    # given
    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    unchanged_item_global_id = graphene.Node.to_global_id(
        "MenuItem", menu_item_list[2].pk
    )

    root_candidate = menu_item_list[0]
    root_candidate_global_id = graphene.Node.to_global_id("MenuItem", root_candidate.pk)

    # Give to the item menu a parent
    previous_parent = menu_item_list[1]
    previous_parent_global_id = graphene.Node.to_global_id(
        "MenuItem", previous_parent.pk
    )
    root_candidate.move_to(previous_parent)
    root_candidate.save()

    assert root_candidate.parent

    moves_input = [
        {"itemId": root_candidate_global_id, "parentId": None, "sortOrder": None}
    ]
    expected_data = {
        "id": menu_global_id,
        "items": [
            {"id": previous_parent_global_id, "parent": None, "children": []},
            {"id": unchanged_item_global_id, "parent": None, "children": []},
            {"id": root_candidate_global_id, "parent": None, "children": []},
        ],
    }

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    menu_data = response["menu"]
    assert not response["errors"]
    assert menu_data

    # Ensure the the item was successfully placed at the root
    # and is now at the bottom of the list (default)
    assert menu_data == expected_data


def test_menu_reorder_cannot_assign_to_ancestor(
    staff_api_client, permission_manage_menus, menu_item_list
):
    # given
    menu_item_list = list(menu_item_list)
    menu_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)

    root = menu_item_list[0]
    root_node_id = graphene.Node.to_global_id("MenuItem", root.pk)

    child = menu_item_list[2]
    child_node_id = graphene.Node.to_global_id("MenuItem", child.pk)

    # Give the child an ancestor
    child.move_to(root)
    child.save()

    # Give the child an ancestor
    child.move_to(root)
    child.save()

    assert not root.parent
    assert child.parent

    moves = [{"itemId": root_node_id, "parentId": child_node_id, "sortOrder": None}]

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    assert response["errors"] == [
        {
            "field": "parentId",
            "message": "Cannot assign a node as child of " "one of its descendants.",
        }
    ]


def test_menu_reorder_cannot_assign_to_itself(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_id = graphene.Node.to_global_id("Menu", menu_item.menu_id)
    node_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    moves = [{"itemId": node_id, "parentId": node_id, "sortOrder": None}]

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves, "menu": menu_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    assert response["errors"] == [
        {"field": "parentId", "message": "Cannot assign a node to itself."}
    ]


def test_menu_cannot_get_menu_item_not_from_same_menu(
    staff_api_client, permission_manage_menus, menu_item
):
    """You shouldn't be able to edit menu items that are not from the menu
    you are actually editing"""

    menu_without_items = Menu.objects.create(
        name="this menu has no items", slug="menu-no-items"
    )

    menu_id = graphene.Node.to_global_id("Menu", menu_without_items.id)
    node_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)
    moves = [{"itemId": node_id}]

    # when
    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU, {"moves": moves, "menu": menu_id}, [permission_manage_menus]
    )

    # then
    assert json.loads(response.content)["data"] == {
        "menuItemMove": {
            "errors": [
                {
                    "field": "item",
                    "message": f"Couldn't resolve to a node: {node_id}",
                }
            ],
            "menu": None,
        }
    }


def test_menu_cannot_pass_an_invalid_menu_item_node_type(
    staff_api_client, staff_user, permission_manage_menus, menu_item
):
    """You shouldn't be able to pass a menu item node
    that is not an actual MenuType."""

    # given
    menu_without_items = Menu.objects.create(
        name="this menu has no items", slug="menu-without-items"
    )

    menu_id = graphene.Node.to_global_id("Menu", menu_without_items.id)
    node_id = graphene.Node.to_global_id("User", staff_user.pk)
    moves = [{"itemId": node_id}]

    # when
    response = staff_api_client.post_graphql(
        QUERY_REORDER_MENU, {"moves": moves, "menu": menu_id}, [permission_manage_menus]
    )

    # then
    assert json.loads(response.content)["data"] == {
        "menuItemMove": {
            "errors": [{"field": "item", "message": "Must receive a MenuItem id."}],
            "menu": None,
        }
    }
