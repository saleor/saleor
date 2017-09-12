from __future__ import unicode_literals
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client

from saleor.userprofile.models import User
from saleor.core.permissions import get_permissions
from saleor.dashboard.groups.forms import PermissionsForm
from saleor.product.models import Product
from saleor.dashboard.staff import views


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


# def test_permission_form(staff_user, staff_group, product_permission_view):
#     assert not staff_user.has_perm("product.view_product")
#     assert not staff_user.has_perm("product.edit_product")
#
#
#     staff_group.permissions.add(product_permission_view)
#     staff_user.groups.add(staff_group)
#
#     del staff_user._perm_cache
#     del staff_user._user_perm_cache
#     assert staff_user.has_perm("product.view_product")
