from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group
from saleor.userprofile.models import User
from saleor.dashboard.group.forms import GroupPermissionsForm
from saleor.dashboard.staff.forms import UserGroupForm


def test_staff_list_view(admin_client):
    response = admin_client.get(reverse('dashboard:staff-list'))
    assert response.status_code == 200


def test_staff_detail_view(admin_client, admin_user):
    response = admin_client.get(reverse('dashboard:staff-details',
                                        args=[admin_user.pk]))
    assert response.status_code == 200


def test_groups_list_view(admin_client):
    response = admin_client.get(reverse('dashboard:group-list'))
    assert response.status_code == 200


def test_group_detail_view(admin_client, staff_group):
    response = admin_client.get(reverse('dashboard:group-details',
                                        args=[staff_group.pk]))
    assert response.status_code == 200


def test_group_create_view(admin_client):
    response = admin_client.get(reverse('dashboard:group-create'))
    assert response.status_code == 200


def test_customers_list_view(admin_client):
    response = admin_client.get(reverse('dashboard:customers'))
    assert response.status_code == 200


def test_customer_detail_view(admin_client, customer_user):
    response = admin_client.get(reverse('dashboard:customer-details',
                                        args=[customer_user.pk]))
    assert response.status_code == 200


def test_staff_cant_access_product_list(staff_client, staff_user):
    assert not staff_user.has_perm("product.view_product")
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 302


def test_staff_can_access_product_list(
        staff_client, staff_user, permission_view_product):
    assert not staff_user.has_perm("product.view_product")
    staff_user.user_permissions.add(permission_view_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("product.view_product")
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 200


def test_staff_cant_access_product_update(
        staff_client, staff_user, product_in_stock):
    assert not staff_user.has_perm("product.edit_product")
    response = staff_client.get(reverse('dashboard:product-update',
                                        args=[product_in_stock.pk]))
    assert response.status_code == 302


def test_staff_can_access_product_update(
        staff_client, staff_user, product_in_stock, permission_edit_product):
    assert not staff_user.has_perm("product.edit_product")
    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("product.edit_product")
    response = staff_client.get(reverse('dashboard:product-update',
                                        args=[product_in_stock.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_product_list(
        staff_client, staff_user, staff_group, permission_view_product):
    assert not staff_user.has_perm("product.view_product")
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_product)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("product.view_product")
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_category_list(
        staff_client, staff_user, staff_group, permission_view_category):
    assert not staff_user.has_perm("product.view_category")
    response = staff_client.get(reverse('dashboard:category-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_category)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("product.view_category")
    response = staff_client.get(reverse('dashboard:category-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_stock_location_list(
        staff_client, staff_user, staff_group, permission_view_stock_location):
    assert not staff_user.has_perm("product.view_stock_location")
    response = staff_client.get(reverse(
        'dashboard:product-stock-location-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_stock_location)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("product.view_stock_location")
    response = staff_client.get(reverse(
        'dashboard:product-stock-location-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_sale_list(
        staff_client, staff_user, staff_group, permission_view_sale):
    assert not staff_user.has_perm("discount.view_sale")
    response = staff_client.get(reverse('dashboard:sale-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_sale)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("discount.view_sale")
    response = staff_client.get(reverse('dashboard:sale-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_voucher_list(
        staff_client, staff_user, staff_group, permission_view_voucher):
    assert not staff_user.has_perm("discount.view_voucher")
    response = staff_client.get(reverse('dashboard:voucher-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_voucher)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("discount.view_voucher")
    response = staff_client.get(reverse('dashboard:voucher-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_order_list(
        staff_client, staff_user, staff_group, permission_view_order):
    assert not staff_user.has_perm("order.view_order")
    response = staff_client.get(reverse('dashboard:orders'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_order)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("order.view_order")
    response = staff_client.get(reverse('dashboard:orders'))
    assert response.status_code == 200


def test_staff_group_member_can_view_customers_list(
        staff_client, staff_user, staff_group, permission_view_user):
    assert not staff_user.has_perm("userprofile.view_user")
    response = staff_client.get(reverse('dashboard:customers'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm("userprofile.view_user")
    response = staff_client.get(reverse('dashboard:customers'))
    assert response.status_code == 200


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
    assert response['Location'] == '/dashboard/groups/'


def test_group_detail_form_valid(
        admin_client, staff_group, permission_view_product):
    url = reverse('dashboard:group-details', args=[staff_group.pk])
    data = {'name': 'view product', 'permissions': permission_view_product.pk}
    admin_client.post(url, data)
    assert Group.objects.all().count() == 1
    assert staff_group.permissions.get(pk=permission_view_product.pk)


def test_user_group_form_not_valid(db):
    data = {'groups': 1}
    form = UserGroupForm(data=data)
    assert not form.is_valid()


def test_user_group_form_create_valid(
        admin_client, staff_user, staff_group):
    url = reverse('dashboard:staff-details', args=[staff_user.pk])
    data = {'groups': staff_group.pk}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.groups.count() == 1


def test_user_group_form_create_not_valid(admin_client, staff_user):
    url = reverse('dashboard:staff-details', args=[staff_user.pk])
    data = {'groups': 1}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.groups.count() == 0


def test_delete_group(admin_client, staff_group):
    assert Group.objects.all().count() == 1
    url = reverse('dashboard:group-delete', args=[staff_group.pk])
    data = {'pk': staff_group.pk}
    response = admin_client.post(url, data)
    assert Group.objects.all().count() == 0
    assert response['Location'] == '/dashboard/groups/'


def test_delete_group_no_POST(admin_client, staff_group):
    url = reverse('dashboard:group-delete', args=[staff_group.pk])
    admin_client.get(url)
    assert Group.objects.all().count() == 1
