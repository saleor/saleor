import json
from unittest import mock

import graphene
import pytest
from django.core.exceptions import ValidationError

from .....core.db.locks import AdvisoryLock
from .....menu.error_codes import MenuErrorCode
from .....menu.models import Menu, MenuItem
from ....tests.utils import get_graphql_content
from ...mutations.menu_item_move import MenuItemMove, _MenuMoveOperation

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
    """Test that assigning parents results in the correct item order."""
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
    """Test that assigning and removing parents results in the correct item order."""
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
    """Test that removing and assigning parents results in the correct item order."""
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

    # Ensure the item was successfully placed at the root
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
            "message": "Cannot assign a node as child of one of its descendants.",
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
    message = f"Invalid ID: {node_id}. Expected: MenuItem, received: User."
    assert json.loads(response.content)["data"] == {
        "menuItemMove": {
            "errors": [
                {
                    "field": "item",
                    "message": message,
                }
            ],
            "menu": None,
        }
    }


def test_moves_to_same_parent_keep_tree_consistent(
    staff_api_client, permission_manage_menus, menu_item_list
):
    # given
    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)
    new_parent, first_moved, second_moved = menu_item_list
    parent_global_id = graphene.Node.to_global_id("MenuItem", new_parent.pk)
    moves_input = [
        {
            "itemId": graphene.Node.to_global_id("MenuItem", first_moved.pk),
            "parentId": parent_global_id,
            "sortOrder": None,
        },
        {
            "itemId": graphene.Node.to_global_id("MenuItem", second_moved.pk),
            "parentId": parent_global_id,
            "sortOrder": None,
        },
    ]

    # when
    response = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_REORDER_MENU,
            {"moves": moves_input, "menu": menu_global_id},
            [permission_manage_menus],
        )
    )["data"]["menuItemMove"]

    # then
    assert response["errors"] == []
    new_parent.refresh_from_db()
    first_moved.refresh_from_db()
    second_moved.refresh_from_db()
    assert (new_parent.lft, new_parent.rght) == (1, 6)
    children_intervals = {
        (first_moved.lft, first_moved.rght),
        (second_moved.lft, second_moved.rght),
    }
    assert children_intervals == {(2, 3), (4, 5)}
    assert first_moved.tree_id == new_parent.tree_id
    assert second_moved.tree_id == new_parent.tree_id


def test_change_parent_operation_refreshes_stale_parent(menu_item_list):
    # given
    new_parent, temp_child, moved_item = menu_item_list
    temp_child.parent = new_parent
    temp_child.save()
    stale_parent = MenuItem.objects.get(pk=new_parent.pk)
    assert (stale_parent.lft, stale_parent.rght) == (1, 4)
    # Simulate a concurrent writer renumbering the tree after the parent was
    # fetched - deleting the child shrinks the parent's interval to (1, 2).
    temp_child.refresh_from_db()
    temp_child.delete()
    operation = _MenuMoveOperation(
        menu_item=moved_item,
        parent_changed=True,
        new_parent=stale_parent,
        sort_order=None,
    )

    # when
    MenuItemMove.perform_change_parent_operation(operation)

    # then
    new_parent.refresh_from_db()
    moved_item.refresh_from_db()
    assert (new_parent.lft, new_parent.rght) == (1, 4)
    assert (moved_item.lft, moved_item.rght) == (2, 3)
    assert moved_item.parent_id == new_parent.pk
    assert moved_item.tree_id == new_parent.tree_id


def test_change_parent_operation_racing_cycle_raises_validation_error(menu_item_list):
    # given
    new_parent, moved_item, _unchanged_item = menu_item_list
    stale_parent = MenuItem.objects.get(pk=new_parent.pk)
    # Simulate a concurrent writer making the target a child of the moved
    # item after the target was fetched, so the move would form a cycle.
    new_parent.parent = moved_item
    new_parent.save()
    operation = _MenuMoveOperation(
        menu_item=moved_item,
        parent_changed=True,
        new_parent=stale_parent,
        sort_order=None,
    )

    # when
    with pytest.raises(ValidationError) as exc_info:
        MenuItemMove.perform_change_parent_operation(operation)

    # then
    errors = exc_info.value.error_dict["parent_id"]
    assert len(errors) == 1
    assert errors[0].code == MenuErrorCode.CANNOT_ASSIGN_NODE.value
    assert errors[0].message == (
        "A node may not be made a child of any of its descendants."
    )
    moved_item.refresh_from_db()
    new_parent.refresh_from_db()
    assert moved_item.parent_id is None
    assert new_parent.parent_id == moved_item.pk


def test_takes_menu_item_tree_lock_before_move(
    staff_api_client,
    permission_manage_menus,
    menu_item_list,
    assert_advisory_lock_before_tree_write,
):
    # given
    menu_item_list = list(menu_item_list)
    menu_global_id = graphene.Node.to_global_id("Menu", menu_item_list[0].menu_id)
    new_parent = menu_item_list[0]
    moved_item = menu_item_list[2]
    moves_input = [
        {
            "itemId": graphene.Node.to_global_id("MenuItem", moved_item.pk),
            "parentId": graphene.Node.to_global_id("MenuItem", new_parent.pk),
            "sortOrder": None,
        }
    ]
    variables = {"moves": moves_input, "menu": menu_global_id}

    # when
    with assert_advisory_lock_before_tree_write(
        AdvisoryLock.MENU_ITEM_TREE, MenuItem._meta.db_table
    ):
        response = staff_api_client.post_graphql(
            QUERY_REORDER_MENU, variables, [permission_manage_menus]
        )

    # then
    content = get_graphql_content(response)
    assert content["data"]["menuItemMove"]["errors"] == []
    moved_item.refresh_from_db(fields=("parent",))
    assert moved_item.parent_id == new_parent.pk
