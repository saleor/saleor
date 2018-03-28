import json

import pytest
from django.urls import reverse

from saleor.menu.models import Menu, MenuItem
from ..utils import get_redirect_location


@pytest.mark.django_db
def test_view_menu_list(admin_client, menu):
    url = reverse('dashboard:menu-list')

    response = admin_client.get(url)

    menu_list = response.context['menus'].object_list
    assert response.status_code == 200
    assert menu in menu_list
    assert len(menu_list) == Menu.objects.count()


@pytest.mark.django_db
def test_view_menu_create(admin_client):
    menus_before = Menu.objects.count()
    url = reverse('dashboard:menu-add')
    data = {'slug': 'new-menu'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:menu-list')
    assert Menu.objects.count() == menus_before + 1


@pytest.mark.django_db
def test_view_menu_create_not_valid(admin_client):
    menus_before = Menu.objects.count()
    url = reverse('dashboard:menu-add')
    data = {}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert Menu.objects.count() == menus_before


@pytest.mark.django_db
def test_view_menu_edit(admin_client, menu):
    url = reverse('dashboard:menu-edit', kwargs={'pk': menu.pk})
    slug = 'navbar2'
    data = {'slug': slug}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse('dashboard:menu-detail', kwargs={'pk': menu.pk})
    assert get_redirect_location(response) == redirect_url
    menu.refresh_from_db()
    assert menu.slug == slug


@pytest.mark.django_db
def test_view_menu_detail(admin_client, menu):
    url = reverse('dashboard:menu-detail', kwargs={'pk': menu.pk})

    response = admin_client.post(url)

    assert response.status_code == 200
    assert response.context['menu'] == menu


@pytest.mark.django_db
def test_view_menu_delete(admin_client, menu):
    menus_before = Menu.objects.count()
    url = reverse('dashboard:menu-delete', kwargs={'pk': menu.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:menu-list')
    assert Menu.objects.count() == menus_before - 1


@pytest.mark.django_db
def test_view_menu_item_create(admin_client, menu, default_category):
    url = reverse('dashboard:menu-item-add', kwargs={'menu_pk': menu.pk})
    linked_object = str(default_category.id) + '_Category'
    data = {'name': 'Link', 'linked_object': linked_object}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse('dashboard:menu-detail', kwargs={'pk': menu.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 1
    menu_item = MenuItem.objects.first()
    assert menu_item.sort_order == 0


@pytest.mark.django_db
def test_view_menu_item_create_with_parent(
        admin_client, menu, menu_item, default_category):
    url = reverse(
        'dashboard:menu-item-add',
        kwargs={'menu_pk': menu.pk, 'root_pk': menu_item.pk})
    linked_object = str(default_category.id) + '_Category'
    data = {'name': 'Link 2', 'linked_object': linked_object}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:menu-item-detail',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 2
    new_menu_item = MenuItem.objects.get(name='Link 2')
    assert new_menu_item.parent == menu_item
    assert new_menu_item.sort_order == 0


@pytest.mark.django_db
def test_view_menu_item_create_not_valid(admin_client, menu):
    url = reverse('dashboard:menu-item-add', kwargs={'menu_pk': menu.pk})
    data = {}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert MenuItem.objects.count() == 0


@pytest.mark.django_db
def test_view_menu_item_edit(admin_client, menu, menu_item, default_category):
    url = reverse(
        'dashboard:menu-item-edit',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    linked_object = str(default_category.id) + '_Category'
    data = {'name': 'New link', 'linked_object': linked_object}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:menu-item-detail',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 1
    menu_item.refresh_from_db()
    assert menu_item.name == 'New link'


@pytest.mark.django_db
def test_view_menu_item_delete(admin_client, menu, menu_item):
    url = reverse(
        'dashboard:menu-item-delete',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    redirect_url = reverse('dashboard:menu-detail', kwargs={'pk': menu.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 0


@pytest.mark.django_db
def test_view_menu_item_delete_with_parent(admin_client, menu, menu_item):
    new_menu_item = MenuItem.objects.create(
        menu=menu, name='New Link', url='http://example.com/',
        parent=menu_item)
    url = reverse(
        'dashboard:menu-item-delete',
        kwargs={'menu_pk': menu.pk, 'item_pk': new_menu_item.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:menu-item-detail',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 1


@pytest.mark.django_db
def test_view_menu_item_detail(admin_client, menu, menu_item):
    url = reverse(
        'dashboard:menu-item-detail',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})

    response = admin_client.post(url)

    assert response.status_code == 200
    assert response.context['menu'] == menu
    assert response.context['menu_item'] == menu_item


@pytest.mark.django_db
def test_view_ajax_reorder_menu_items(admin_client, menu, menu_with_items):
    items = menu_with_items.items.filter(parent=None)
    order_before = [item.pk for item in items]
    ordered_menu_items = list(reversed(order_before))
    url = reverse(
        'dashboard:menu-items-reorder', kwargs={'menu_pk': menu.pk})
    data = {'ordered_menu_items': ordered_menu_items}

    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    menu_with_items.refresh_from_db()
    items = menu_with_items.items.filter(parent=None)
    order_after = [item.pk for item in items]
    assert order_after == ordered_menu_items


@pytest.mark.integration
@pytest.mark.django_db
def test_view_ajax_reorder_menu_items_with_parent(
        admin_client, menu, menu_with_items):
    items = menu_with_items.items.exclude(parent=None)
    order_before = [item.pk for item in items]
    ordered_menu_items = list(reversed(order_before))
    menu_item = items.first().parent
    url = reverse(
        'dashboard:menu-items-reorder',
        kwargs={'menu_pk': menu.pk, 'root_pk': menu_item.pk})
    data = {'ordered_menu_items': ordered_menu_items}

    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    menu_with_items.refresh_from_db()
    items = menu_with_items.items.exclude(parent=None)
    order_after = [item.pk for item in items]
    assert order_after == ordered_menu_items


@pytest.mark.integration
@pytest.mark.django_db
def test_view_ajax_menu_links(
        admin_client, collection, default_category, page):
    collection_repr = {
        'id': str(collection.pk) + '_' + 'Collection',
        'text': str(collection)}
    category_repr = {
        'id': str(default_category.pk) + '_' + 'Category',
        'text': str(default_category)}
    page_repr = {
        'id': str(page.pk) + '_' + 'Page',
        'text': str(page)}
    groups = [
        {'text': 'Collection', 'children': [collection_repr]},
        {'text': 'Category', 'children': [category_repr]},
        {'text': 'Page', 'children': [page_repr]}
    ]

    url = reverse('dashboard:ajax-menu-links')
    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))

    assert response.status_code == 200
    assert resp_decoded == {'results': groups}
