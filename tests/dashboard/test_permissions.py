from __future__ import unicode_literals

import pytest
from mock import Mock

from saleor.dashboard.staff.forms import PermissionsForm
from saleor.core.permissions import (update_permissions,)


def test_staff_list(staff_client):
    pass


def test_permission_form(default_permissions_choices):
    data = {
        "products": default_permissions_choices
    }
    form = PermissionsForm(data)
    assert form.is_valid()


def test_superuser_permissions(admin_user):
    assert admin_user.has_perm("product.view_product")
    assert admin_user.has_perm("product.edit_product")


# def test_staffuser_permissions(staff_user, default_permissions_choices):
#     assert not staff_user.has_perm("product.view_product")
#     assert not staff_user.has_perm("product.edit_product")
#
#     # Adding permissions
#     print staff_user.pk
#     update_permissions(staff_user, staff_user.pk, "product",
#                        default_permissions_choices)
#     assert staff_user.has_perm("product.view_product")
#     assert staff_user.has_perm("product.edit_product")
