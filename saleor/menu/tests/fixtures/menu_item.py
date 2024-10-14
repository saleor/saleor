import pytest

from ...models import MenuItem


@pytest.fixture
def menu_item(menu):
    return MenuItem.objects.create(menu=menu, name="Link 1", url="http://example.com/")


@pytest.fixture
def menu_item_list(menu):
    menu_item_1 = MenuItem.objects.create(menu=menu, name="Link 1")
    menu_item_2 = MenuItem.objects.create(menu=menu, name="Link 2")
    menu_item_3 = MenuItem.objects.create(menu=menu, name="Link 3")
    return menu_item_1, menu_item_2, menu_item_3
