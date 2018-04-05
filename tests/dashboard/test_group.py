from django.contrib.auth.models import Group
from django.urls import reverse

from saleor.dashboard.group.forms import GroupPermissionsForm


def test_group_permissions_form_not_valid(db):
    data = {'name': 1, 'permissions': 2}
    form = GroupPermissionsForm(data=data)
    assert not form.is_valid()


def test_group_create_form_not_valid(admin_client):
    url = reverse('dashboard:group-create')
    data = {'name': 1, 'permissions': 2}
    response = admin_client.post(url, data)
    assert Group.objects.all().count() == 0
    assert response.template_name == 'dashboard/group/detail.html'


def test_group_create_form_valid(admin_client, permission_view_product):
    url = reverse('dashboard:group-create')
    data = {'name': 'view product', 'permissions': permission_view_product.pk}
    response = admin_client.post(url, data)
    assert Group.objects.all().count() == 1
    assert response['Location'] == reverse('dashboard:group-list')


def test_group_detail_form_valid(
        admin_client, staff_group, permission_view_product):
    url = reverse('dashboard:group-details', args=[staff_group.pk])
    data = {'name': 'view product', 'permissions': permission_view_product.pk}
    admin_client.post(url, data)
    assert Group.objects.all().count() == 1
    assert staff_group.permissions.get(pk=permission_view_product.pk)


def test_delete_group(admin_client, staff_group):
    assert Group.objects.all().count() == 1
    url = reverse('dashboard:group-delete', args=[staff_group.pk])
    data = {'pk': staff_group.pk}
    response = admin_client.post(url, data)
    assert Group.objects.all().count() == 0
    assert response['Location'] == reverse('dashboard:group-list')


def test_delete_group_no_post(admin_client, staff_group):
    url = reverse('dashboard:group-delete', args=[staff_group.pk])
    admin_client.get(url)
    assert Group.objects.all().count() == 1
