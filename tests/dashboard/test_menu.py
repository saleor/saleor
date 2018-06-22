import json

import pytest
from django.urls import reverse

from saleor.dashboard.menu.forms import AssignMenuForm
from saleor.dashboard.menu.utils import update_menu_item_linked_object
from saleor.menu.models import Menu, MenuItem

from ..utils import get_redirect_location


def test_assign_menu_form(admin_user, menu, site_settings):
    data = {'top_menu': menu.pk, 'bottom_menu': ''}
    form = AssignMenuForm(data=data, user=admin_user, instance=site_settings)
    assert not form.fields['top_menu'].disabled
    assert not form.fields['bottom_menu'].disabled
    assert form.is_valid()


def test_assign_menu_form_no_permission(staff_user, menu, site_settings):
    data = {'top_menu': menu.pk, 'bottom_menu': ''}
    form = AssignMenuForm(data=data, user=staff_user, instance=site_settings)
    assert form.fields['top_menu'].disabled
    assert form.fields['bottom_menu'].disabled
    assert form.is_valid()


def test_view_menu_list_assign_new_menu_to_settings(
        admin_client, menu, site_settings):
    url = reverse('dashboard:menu-list')
    top_menu = menu
    menu.pk = None
    menu.save()
    bottom_menu = Menu.objects.exclude(pk=menu.pk).first()
    site_settings.bottom_menu = bottom_menu
    site_settings.save()
    assert site_settings.bottom_menu

    data = {'top_menu': top_menu.pk, 'bottom_menu': ''}
    response = admin_client.post(url, data=data)

    assert response.status_code == 302
    assert get_redirect_location(response) == url

    site_settings.refresh_from_db()
    assert site_settings.top_menu == top_menu
    assert not site_settings.bottom_menu


def test_view_menu_list_assign_new_menu_to_settings_no_edit_permission(
        staff_client, menu, site_settings, permission_view_menu, staff_group,
        staff_user):
    staff_group.permissions.add(permission_view_menu)
    staff_user.groups.add(staff_group)

    url = reverse('dashboard:menu-list')
    data = {'top_menu': menu.pk, 'bottom_menu': ''}
    response = staff_client.post(url, data=data)
    assert response.status_code == 200

    site_settings.refresh_from_db()
    assert not site_settings.top_menu
    assert not site_settings.bottom_menu


def test_view_menu_list(admin_client, menu):
    url = reverse('dashboard:menu-list')

    response = admin_client.get(url)

    menu_list = response.context['menus'].object_list
    assert response.status_code == 200
    assert menu in menu_list
    assert len(menu_list) == Menu.objects.count()


def test_view_menu_create(admin_client):
    menus_before = Menu.objects.count()
    url = reverse('dashboard:menu-add')
    data = {'name': 'Summer Collection'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:menu-list')
    assert Menu.objects.count() == menus_before + 1


def test_view_menu_create_not_valid(admin_client):
    menus_before = Menu.objects.count()
    url = reverse('dashboard:menu-add')
    data = {}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert Menu.objects.count() == menus_before


def test_view_menu_edit(admin_client, menu):
    url = reverse('dashboard:menu-edit', kwargs={'pk': menu.pk})
    name = 'Summer Collection'
    data = {'name': name}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse('dashboard:menu-details', kwargs={'pk': menu.pk})
    assert get_redirect_location(response) == redirect_url
    menu.refresh_from_db()
    assert menu.name == name


def test_view_menu_details(admin_client, menu):
    url = reverse('dashboard:menu-details', kwargs={'pk': menu.pk})

    response = admin_client.post(url)

    assert response.status_code == 200
    assert response.context['menu'] == menu


def test_view_menu_delete(admin_client, menu):
    menus_before = Menu.objects.count()
    url = reverse('dashboard:menu-delete', kwargs={'pk': menu.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:menu-list')
    assert Menu.objects.count() == menus_before - 1


def test_view_menu_item_create(admin_client, menu, default_category):
    url = reverse('dashboard:menu-item-add', kwargs={'menu_pk': menu.pk})
    linked_object = str(default_category.id) + '_Category'
    data = {'name': 'Link', 'linked_object': linked_object}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse('dashboard:menu-details', kwargs={'pk': menu.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 1
    menu_item = MenuItem.objects.first()
    assert menu_item.sort_order == 0


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
        'dashboard:menu-item-details',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 2
    new_menu_item = MenuItem.objects.get(name='Link 2')
    assert new_menu_item.parent == menu_item
    assert new_menu_item.sort_order == 0


def test_view_menu_item_create_not_valid(admin_client, menu):
    url = reverse('dashboard:menu-item-add', kwargs={'menu_pk': menu.pk})
    data = {}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert MenuItem.objects.count() == 0


def test_view_menu_item_edit(admin_client, menu, menu_item, default_category):
    url = reverse(
        'dashboard:menu-item-edit',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    linked_object = str(default_category.id) + '_Category'
    data = {'name': 'New link', 'linked_object': linked_object}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    redirect_url = reverse(
        'dashboard:menu-item-details',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 1
    menu_item.refresh_from_db()
    assert menu_item.name == 'New link'


def test_view_menu_item_delete(admin_client, menu, menu_item):
    url = reverse(
        'dashboard:menu-item-delete',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    redirect_url = reverse('dashboard:menu-details', kwargs={'pk': menu.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 0


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
        'dashboard:menu-item-details',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})
    assert get_redirect_location(response) == redirect_url
    assert MenuItem.objects.count() == 1


def test_view_menu_item_details(admin_client, menu, menu_item):
    url = reverse(
        'dashboard:menu-item-details',
        kwargs={'menu_pk': menu.pk, 'item_pk': menu_item.pk})

    response = admin_client.post(url)

    assert response.status_code == 200
    assert response.context['menu'] == menu
    assert response.context['menu_item'] == menu_item


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


def test_update_menu_item_linked_object(menu, default_category, page):
    menu_item = menu.items.create(category=default_category)

    update_menu_item_linked_object(menu_item, page)

    assert menu_item.linked_object == page
    assert menu_item.get_url() == page.get_absolute_url()
    assert not menu_item.category
    assert not menu_item.collection
