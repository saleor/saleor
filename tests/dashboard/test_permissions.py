from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group, Permission

from saleor.userprofile.models import User
from saleor.dashboard.group.forms import GroupPermissionsForm
from saleor.dashboard.staff.forms import UserGroupForm


def test_superuser_permissions(admin_user):
    assert admin_user.has_perm("product.view_product")
    assert admin_user.has_perm("product.edit_product")


def test_superuser(admin_user):
    assert isinstance(admin_user, User)


def test_staff_list_view(admin_client):
    response = admin_client.get('/dashboard/staff/')
    assert response.status_code == 200


def test_staff_detail_view(admin_client, admin_user):
    response = admin_client.get('/dashboard/staff/%s/' % admin_user.pk)
    assert response.status_code == 200


def test_groups_list_view(admin_client):
    response = admin_client.get('/dashboard/groups/')
    assert response.status_code == 200


def test_group_detail_view(admin_client, staff_group):
    response = admin_client.get('/dashboard/groups/%s/' % staff_group.pk)
    assert response.status_code == 200


def test_group_create_view(admin_client):
    response = admin_client.get('/dashboard/groups/group-create/')
    assert response.status_code == 200


def test_customers_list_view(admin_client):
    response = admin_client.get('/dashboard/customers/')
    assert response.status_code == 200


def test_customer_detail_view(admin_client, customer_user):
    response = admin_client.get('/dashboard/customers/%s/' % customer_user.pk)
    assert response.status_code == 200


def test_staff_cant_access_product_list(staff_client, staff_user):
    assert not staff_user.has_perm("product.view_product")
    response = staff_client.get('/dashboard/products/')
    assert response.status_code == 302


def test_staff_can_access_product_list(
        staff_client, staff_user, permission_view_product):
    assert not staff_user.has_perm("product.view_product")
    staff_user.user_permissions.add(permission_view_product)
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.view_product")
    response = staff_client.get('/dashboard/products/')
    assert response.status_code == 200


def test_staff_cant_access_product_update(
        staff_client, staff_user, product_in_stock):
    assert not staff_user.has_perm("product.edit_product")
    response = staff_client.get(
        "/dashboard/products/%s/update/" % product_in_stock.pk)
    assert response.status_code == 302


def test_staff_can_access_product_update(
        staff_client, staff_user, product_in_stock, permission_edit_product):
    assert not staff_user.has_perm("product.edit_product")
    staff_user.user_permissions.add(permission_edit_product)
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.edit_product")
    response = staff_client.get(
        "/dashboard/products/%s/update/" % product_in_stock.pk)
    assert response.status_code == 200


def test_staff_group_member_can_view_products(
        staff_client, staff_user, staff_group, permission_view_product):
    assert not staff_user.has_perm("product.view_product")
    response = staff_client.get('/dashboard/products/')
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_product)
    staff_user.groups.add(staff_group)
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    # assert staff_user.has_perm("product.view_product")
    response = staff_client.get('/dashboard/products/')
    assert response.status_code == 200


def test_group_permissions_form_not_valid(db):
    data = {'name': 1, 'permissions': 2}
    form = GroupPermissionsForm(data=data)
    assert not form.is_valid()


def test_group_create_form_not_valid(admin_client):
    admin_client.post(
        reverse('dashboard:group-create'),
        {'name': 1, 'permissions': 2}
    )
    assert Group.objects.all().count() == 0


# def test_group_create_view_not_valid(admin_client, permission_view_product):
#     admin_client.post(
#         reverse('dashboard:group-create'),
#         {'name': 'view product', 'permissions': permission_view_product}
#     )
#     assert Group.objects.all().count() == 1


def test_user_group_form_not_valid(db):
    data = {'groups': 1}
    form = UserGroupForm(data=data)
    assert not form.is_valid()
