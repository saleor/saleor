from __future__ import unicode_literals
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client

from saleor.userprofile.models import User
from saleor.core.permissions import get_permissions
from saleor.dashboard.groups.forms import PermissionsForm
from saleor.product.models import Product


def test_superuser_permissions(admin_user):
    assert admin_user.has_perm("product.view_product")
    assert admin_user.has_perm("product.edit_product")


def test_superuser(admin_user):
    assert isinstance(admin_user, User)


# def test_permission_form(staff_user, staff_group, product_permission_view):
#     assert not staff_user.has_perm("product.view_product")
#     assert not staff_user.has_perm("product.edit_product")
#
#     staff_user.groups.add(staff_group)
#     staff_group.permissions.add(product_permission_view)
#
#     assert not staff_user.has_perm("product.view_product")
