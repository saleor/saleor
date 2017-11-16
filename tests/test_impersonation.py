from django.core.urlresolvers import reverse
import pytest

from saleor.userprofile.impersonate import can_impersonate
from saleor.userprofile.models import User

def test_staff_with_permission_can_impersonate(
        staff_client, customer_user, staff_user, permission_impersonate_user,
        staff_group):
    staff_group.permissions.add(permission_impersonate_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    response = staff_client.get(reverse('impersonate-start',
                                args=[customer_user.pk]), follow=True)
    assert response.context['user'] == customer_user
    assert response.context['user'].is_impersonate
    assert response.context['request'].impersonator == staff_user
