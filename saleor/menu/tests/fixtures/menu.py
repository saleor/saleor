import pytest

from ...models import Menu


@pytest.fixture
def menu(db):
    return Menu.objects.get_or_create(name="test-navbar", slug="test-navbar")[0]


@pytest.fixture
def menu_with_items(menu, category, published_collection):
    menu.items.create(name="Link 1", url="http://example.com/")
    menu_item = menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name=category.name, category=category, parent=menu_item)
    menu.items.create(
        name=published_collection.name,
        collection=published_collection,
        parent=menu_item,
    )
    return menu
