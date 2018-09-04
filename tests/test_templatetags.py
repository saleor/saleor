import json

from django.urls import reverse
from saleor.core.templatetags.shop import get_sort_by_url, menu


def test_menu(menu_with_items):
    result = menu()
    assert result == {'horizontal': False, 'menu_items': []}

    result = menu(menu_with_items)
    assert result['menu_items'] == json.loads(menu_with_items.json_content)
