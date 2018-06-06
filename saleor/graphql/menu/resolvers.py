from ...menu import models


def resolve_menus(info):
    return models.Menu.objects.all().distinct()


def resolve_menu_items(info):
    return models.MenuItem.objects.all().distinct()
