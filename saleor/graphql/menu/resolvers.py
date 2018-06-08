from ...menu import models


def resolve_menus(info):
    return models.Menu.objects.all()


def resolve_menu_items(info):
    return models.MenuItem.objects.all()
