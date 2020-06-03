from saleor.menu.utils import get_menu_item_as_dict


def menu_item_to_json(menu_item):
    """Transforms a menu item to a JSON representation as used in the storefront."""
    item_json = get_menu_item_as_dict(menu_item)
    item_json["child_items"] = []
    return item_json
