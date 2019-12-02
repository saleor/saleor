from saleor.core.templatetags.shop import menu


def test_menu(menu_with_items):
    result = menu()
    assert result == {"horizontal": False, "menu_items": []}

    result = menu(menu_with_items)
    assert result["menu_items"] == menu_with_items.json_content
