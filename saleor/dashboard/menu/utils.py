from ...page.models import Page
from ...product.models import Category, Collection


def update_menu_item_linked_object(menu_item, linked_object):
    """Assign new linked object to a menu item. Clear other links."""
    menu_item.category = None
    menu_item.collection = None
    menu_item.page = None

    if isinstance(linked_object, Category):
        menu_item.category = linked_object
    elif isinstance(linked_object, Collection):
        menu_item.collection = linked_object
    elif isinstance(linked_object, Page):
        menu_item.page = linked_object

    return menu_item.save()
