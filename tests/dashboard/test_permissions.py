from __future__ import unicode_literals

from saleor.dashboard.staff.forms import PermissionsForm
from saleor.core.permissions import (update_permissions,)


def test_permission_form(default_permissions_choices):
    data = {
        "products": default_permissions_choices
    }
    form = PermissionsForm(data)
    assert form.is_valid()


def test_superuser_permissions(admin_user):
    assert admin_user.has_perm("product.view_product")
    assert admin_user.has_perm("product.edit_product")


def test_staffuser_permissions(staff_user, default_permissions_choices):
    assert not staff_user.has_perm("product.view_product")
    assert not staff_user.has_perm("product.edit_product")

    # Adding permissions
    print staff_user.pk
    update_permissions(staff_user, staff_user.pk, "product",
                       default_permissions_choices)
    # Users permissions are cached so we need to delete cache before check
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.view_product")
    assert staff_user.has_perm("product.edit_product")
