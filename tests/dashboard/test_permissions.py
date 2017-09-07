from __future__ import unicode_literals

from saleor.dashboard.staff.forms import PermissionsForm
from saleor.product.models import Product
from saleor.core.permissions import ( get_user_permissions,
    update_permissions, build_permission_choices)


def test_permission_form(default_permissions):
    data = {
        "products": default_permissions
    }
    form = PermissionsForm(data)
    assert form.is_valid()


def test_build_permission_choices():
    choices = build_permission_choices(Product)
    assert ("view_product", "View in Dashboard") in choices
    assert ("edit_product", "Edit in Dashboard") in choices


def test_superuser_permissions(admin_user):
    assert admin_user.has_perm("product.view_product")
    assert admin_user.has_perm("product.edit_product")


def test_staffuser_permissions(staff_user, default_permissions):
    assert not staff_user.has_perm("product.view_product")
    assert not staff_user.has_perm("product.edit_product")

    # Adding permissions
    update_permissions(staff_user, "product", default_permissions)
    # Users permissions are cached so we need to delete cache before check
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.view_product")
    assert staff_user.has_perm("product.edit_product")


def test_get_user_permissions(staff_user, default_permissions):
    assert not staff_user.has_perm("product.view_product")
    assert not staff_user.has_perm("product.edit_product")

    # Adding permissions
    update_permissions(staff_user, "product", default_permissions)
    # Users permissions are cached so we need to delete cache before check
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.view_product")
    assert staff_user.has_perm("product.edit_product")

    data = get_user_permissions(staff_user)
    assert "product" in data.keys()
    assert "view_product" in data["product"]


def test_change_user_permissions(staff_user, default_permissions,
                                 changed_permissions):
    assert not staff_user.has_perm("product.view_product")
    assert not staff_user.has_perm("product.edit_product")

    # Adding permissions
    update_permissions(staff_user, "product", default_permissions)
    # Users permissions are cached so we need to delete cache before check
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.view_product")
    assert staff_user.has_perm("product.edit_product")

    update_permissions(staff_user, "product", changed_permissions)
    del staff_user._perm_cache
    del staff_user._user_perm_cache
    assert staff_user.has_perm("product.view_product")
    assert not staff_user.has_perm("product.edit_product")
