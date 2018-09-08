import json

from django.urls import reverse
from saleor.core.templatetags.shop import get_sort_by_url, menu


def test_sort_by_url_ascending(admin_client, category):
    url = reverse(
        'product:category',
        kwargs={'slug': category.slug, 'category_id': category.id})
    response = admin_client.get(url)
    result = get_sort_by_url(response.context, 'name')
    expected = url + '?sort_by=name'
    assert result == expected


def test_sort_by_url_descending(admin_client, category):
    url = reverse(
        'product:category',
        kwargs={'slug': category.slug, 'category_id': category.id})
    response = admin_client.get(url)
    result = get_sort_by_url(response.context, 'name', descending=True)
    expected = url + '?sort_by=-name'
    assert result == expected


def test_menu(menu_with_items):
    result = menu()
    assert result == {'horizontal': False, 'menu_items': []}

    result = menu(menu_with_items)
    assert result['menu_items'] == json.loads(menu_with_items.json_content)
