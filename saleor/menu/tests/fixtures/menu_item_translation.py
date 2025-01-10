import pytest

from ...models import MenuItemTranslation


@pytest.fixture
def menu_item_translation_fr(menu_item):
    return MenuItemTranslation.objects.create(
        language_code="fr", menu_item=menu_item, name="French manu item name"
    )
