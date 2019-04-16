from unittest.mock import Mock, patch

from django.urls import reverse

from saleor.product.models import Category
from tests.utils import create_image


def test_category_list(admin_client, category):
    url = reverse('dashboard:category-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_category_add(monkeypatch, admin_client):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    assert Category.objects.count() == 0
    url = reverse('dashboard:category-add')
    data = {'name': 'Cars', 'description': 'Fastest cars'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 1
    assert mock_create_thumbnails.call_count == 0


def test_category_add_with_background_image(
        monkeypatch, admin_client, media_root):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    url = reverse('dashboard:category-add')
    image, image_name = create_image()
    data = {
        'name': 'Cars',
        'description': 'Super fast!',
        'background_image': image}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200

    mock_create_thumbnails.assert_called_once_with(Category.objects.last().pk)


def test_category_add_not_valid(admin_client):
    assert Category.objects.count() == 0
    url = reverse('dashboard:category-add')
    data = {}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 0


def test_category_add_subcategory(admin_client, category):
    assert Category.objects.count() == 1
    url = reverse('dashboard:category-add',
                  kwargs={'root_pk': category.pk})
    data = {'name': 'Cars', 'description': 'Fastest cars'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 2
    category.refresh_from_db()
    subcategories = category.get_children()
    assert len(subcategories) == 1
    assert subcategories[0].name == 'Cars'


def test_category_edit(monkeypatch, admin_client, category):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    assert Category.objects.count() == 1
    url = reverse('dashboard:category-edit',
                  kwargs={'root_pk': category.pk})
    data = {'name': 'Cars', 'description': 'Super fast!'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Category.objects.count() == 1
    assert Category.objects.all()[0].name == 'Cars'
    assert mock_create_thumbnails.call_count == 0


def test_category_edit_with_background_image(
        monkeypatch, admin_client, category, media_root):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.dashboard.category.forms.'
         'create_category_background_image_thumbnails.delay'),
        mock_create_thumbnails)

    url = reverse('dashboard:category-edit', kwargs={'root_pk': category.pk})
    image, image_name = create_image()
    data = {
        'name': 'Cars',
        'description': 'Super fast!',
        'background_image': image}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200

    category.refresh_from_db()
    assert category.background_image
    mock_create_thumbnails.assert_called_once_with(category.pk)


def test_category_details(admin_client, category):
    assert Category.objects.count() == 1
    url = reverse('dashboard:category-details',
                  kwargs={'pk': category.pk})
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200


@patch('saleor.dashboard.category.views.get_menus_that_needs_update')
@patch('saleor.dashboard.category.views.update_menus')
def test_category_delete(
        mock_update_menus, mock_get_menus, admin_client, category):
    assert Category.objects.count() == 1
    mock_get_menus.return_value = [1]
    url = reverse('dashboard:category-delete',
                  kwargs={'pk': category.pk})
    response = admin_client.post(url, follow=True)
    assert mock_update_menus.called

    assert response.status_code == 200
    assert Category.objects.count() == 0


@patch('saleor.dashboard.category.views.get_menus_that_needs_update')
@patch('saleor.dashboard.category.views.update_menus')
def test_category_delete_menus_not_updated(
        mock_update_menus, mock_get_menus, admin_client, category):
    url = reverse('dashboard:category-delete',
                  kwargs={'pk': category.pk})
    mock_get_menus.return_value = []
    response = admin_client.post(url, follow=True)
    assert response.status_code == 200
    assert mock_get_menus.called
    assert not mock_update_menus.called
