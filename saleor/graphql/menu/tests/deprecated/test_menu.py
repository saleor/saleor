import warnings

import graphene

from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from .....menu.models import MenuItem
from ....tests.utils import get_graphql_content


def test_menu_items_collection_without_providing_channel(
    user_api_client, menu_item, published_collection
):
    query = """
    query menuitem($id: ID!, $channel: String) {
        menuItem(id: $id, channel: $channel) {
            name
            children {
                name
            }
            collection {
                name
            }
            category {
                id
            }
            page {
                id
            }
            menu {
                id
            }
            url
        }
    }
    """
    menu_item.collection = published_collection
    menu_item.url = None
    menu_item.save()
    child_menu = MenuItem.objects.create(
        menu=menu_item.menu, name="Link 2", url="http://example2.com/", parent=menu_item
    )
    variables = {
        "id": graphene.Node.to_global_id("MenuItem", menu_item.pk),
    }
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(query, variables)
        content = get_graphql_content(response)
        assert any(
            [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
        )

    data = content["data"]["menuItem"]
    assert data["name"] == menu_item.name
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == child_menu.name
    assert data["collection"]["name"] == published_collection.name
    assert not data["category"]
    assert not data["page"]
    assert data["url"] is None
