from ..models import User
from ..utils import remove_staff_member


def test_remove_staff_member_with_orders(staff_user, permission_manage_products, order):
    # given
    order.user = staff_user
    order.save()
    staff_user.user_permissions.add(permission_manage_products)

    # when
    remove_staff_member(staff_user)

    # then
    staff_user = User.objects.get(pk=staff_user.pk)
    assert not staff_user.is_staff
    assert not staff_user.user_permissions.exists()


def test_remove_staff_member(staff_user):
    # when
    remove_staff_member(staff_user)

    # then
    assert not User.objects.filter(pk=staff_user.pk).exists()
