from unittest import mock

from saleor.menu.models import MenuItem, MenuItemTranslation
from saleor.menu.utils import (
    get_menu_as_json,
    get_menu_item_as_dict,
    update_menu,
    update_menus,
)


def test_get_menu_item_as_dict(menu):
    item = MenuItem.objects.create(name="Name", menu=menu, url="http://url.com")
    result = get_menu_item_as_dict(item)
    assert result == {"name": "Name", "url": "http://url.com", "translations": {}}


def test_get_menu_item_as_dict_empty_url():
    item = MenuItem(name="Name")
    result = get_menu_item_as_dict(item)
    assert result == {"name": "Name", "url": "", "translations": {}}


def test_get_menu_item_as_dict_with_translations(menu, collection):
    item = MenuItem.objects.create(name="Name", menu=menu, collection=collection)
    MenuItemTranslation.objects.create(
        menu_item=item, name="Polish Name", language_code="pl"
    )
    result = get_menu_item_as_dict(item)
    assert result == {
        "name": "Name",
        "url": item.url or "",
        "translations": {"pl": {"name": "Polish Name"}},
    }


def test_get_menu_as_json(menu):
    top_item = MenuItem.objects.create(
        menu=menu, name="top item", url="http://topitem.pl"
    )
    child_item = MenuItem.objects.create(
        menu=menu, parent=top_item, name="child item", url="http://childitem.pl"
    )
    grand_child_item = MenuItem.objects.create(
        menu=menu,
        parent=child_item,
        name="grand child item",
        url="http://grandchilditem.pl",
    )
    top_item_data = get_menu_item_as_dict(top_item)
    child_item_data = get_menu_item_as_dict(child_item)
    grand_child_data = get_menu_item_as_dict(grand_child_item)

    child_item_data["child_items"] = [grand_child_data]
    top_item_data["child_items"] = [child_item_data]
    proper_data = [top_item_data]
    assert proper_data == get_menu_as_json(menu)


@mock.patch("saleor.menu.utils.update_menu")
def test_update_menus(mock_update_menu, menu):
    update_menus([menu.pk])
    mock_update_menu.assert_called_once_with(menu)


@mock.patch("saleor.menu.utils.get_menu_as_json")
def test_update_menu(mock_json_menu, menu):
    mock_json_menu.return_value = "Return value"
    update_menu(menu)

    mock_json_menu.assert_called_once_with(menu)
    menu.refresh_from_db()
    assert menu.json_content == "Return value"


def test_menu_item_status(menu, category, collection, page):
    item = MenuItem.objects.create(name="Name", menu=menu)
    assert item.is_public()

    item = MenuItem.objects.create(name="Name", menu=menu, collection=collection)
    assert item.is_public()
    collection.is_published = False
    collection.save()
    item.refresh_from_db()
    assert not item.is_public()

    item = MenuItem.objects.create(name="Name", menu=menu, category=category)
    assert item.is_public()

    item = MenuItem.objects.create(name="Name", menu=menu, page=page)
    assert item.is_public()
    page.is_published = False
    page.save()
    item.refresh_from_db()
    assert not item.is_public()
