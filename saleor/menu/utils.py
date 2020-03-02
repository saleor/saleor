from django.db import transaction

from ..menu.models import Menu


def get_menu_item_as_dict(menu_item):
    data = {}
    data["url"] = menu_item.url or ""
    data["name"] = menu_item.name
    data["translations"] = {
        translated.language_code: {"name": translated.name}
        for translated in menu_item.translations.all()
    }
    return data


def get_menu_as_json(menu):
    """Build a tree structure from top menu items, its children and grandchildren."""
    top_items = menu.items.filter(parent=None).prefetch_related(
        "category",
        "page",
        "collection",
        "children__category",
        "children__page",
        "children__collection",
        "children__children__category",
        "children__children__page",
        "children__children__collection",
        "translations",
        "children__translations",
        "children__children__translations",
    )
    menu_data = []
    for item in top_items:
        top_item_data = get_menu_item_as_dict(item)
        top_item_data["child_items"] = []
        children = item.children.all()
        for child in children:
            child_data = get_menu_item_as_dict(child)
            grand_children = child.children.all()
            grand_children_data = [
                get_menu_item_as_dict(grand_child) for grand_child in grand_children
            ]
            child_data["child_items"] = grand_children_data
            top_item_data["child_items"].append(child_data)
        menu_data.append(top_item_data)
    return menu_data


@transaction.atomic
def update_menus(menus_pk):
    menus = Menu.objects.filter(pk__in=menus_pk)
    for menu in menus:
        update_menu(menu)


def update_menu(menu):
    menu.json_content = get_menu_as_json(menu)
    menu.save(update_fields=["json_content"])
