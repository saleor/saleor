from django.urls import reverse

from saleor.core.templatetags.shop import get_sort_by_url, menu
from saleor.core.templatetags.status import (
    LABEL_SUCCESS, render_page_availability)


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
    assert result['menu_items'] == menu_with_items.json_content


def test_render_page_availability(page):
    page_ctx = render_page_availability(page)
    assert page_ctx == {
        'page': page, 'is_visible': True, 'label_cls': LABEL_SUCCESS}

    page.is_published = False
    page.save()
    page_ctx = render_page_availability(page)
    assert page_ctx == {'page': page, 'is_visible': False}
