from collections import defaultdict

from ...menu.models import Menu, MenuItem
from ..core.dataloaders import DataLoader


class MenuByIdLoader(DataLoader):
    context_key = "menu_by_id"

    def batch_load(self, keys):
        menus = Menu.objects.in_bulk(keys)
        return [menus.get(menu_id) for menu_id in keys]


class MenuItemByIdLoader(DataLoader):
    context_key = "menuitem_by_id"

    def batch_load(self, keys):
        menu_items = MenuItem.objects.in_bulk(keys)
        return [menu_items.get(menu_item_id) for menu_item_id in keys]


class MenuItemsByParentMenuLoader(DataLoader):
    context_key = "menuitems_by_parent_menu"

    def batch_load(self, keys):
        menu_items = MenuItem.objects.filter(menu_id__in=keys, level=0)
        items_map = defaultdict(list)
        for menu_item in menu_items:
            items_map[menu_item.menu_id].append(menu_item)
        return [items_map[menu_id] for menu_id in keys]


class MenuItemChildrenLoader(DataLoader):
    context_key = "menuitem_children"

    def batch_load(self, keys):
        menu_items = MenuItem.objects.filter(parent_id__in=keys)
        items_map = defaultdict(list)
        for menu_item in menu_items:
            items_map[menu_item.parent_id].append(menu_item)
        return [items_map[menu_item_id] for menu_item_id in keys]
