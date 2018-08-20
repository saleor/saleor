from django.urls import reverse

from saleor.account.models import User
from saleor.dashboard.organization.forms import OrganizationDeleteForm


def test_view_delete_organization(admin_client, authorized_client, organization):
    url = reverse('dashboard:organization-delete', args=[organization.pk])
    data = {'csrf': 'exampledata'}
    response = authorized_client.get(url, data=data)
    assert response.status_code == 302

    response = admin_client.get(url, data=data)
    assert response.status_code == 200


def test_form_delete_organization(
        organization_factory, customer_user, staff_user, group_factory):
    # Can only delete a organization that doesn't have customers, and only with
    # sufficient permissions.
    data = {'csrf': 'example-data'}
    organization = organization_factory('Lonely Inc.', '123 Somewhere')
    form = OrganizationDeleteForm(data, instance=organization, user=staff_user)
    assert not form.is_valid()

    group = group_factory('Organization Manager', 'manage_organizations')
    staff_user.groups.add(group)
    staff_user = User.objects.get(pk=staff_user.pk)
    form = OrganizationDeleteForm(data, instance=organization, user=staff_user)
    assert form.is_valid()

    # Deleting non-empty organization not okay even with edit permission
    organization = organization_factory('Whoobee Inc.', '123 Somewhere')
    customer_user.organization = organization
    customer_user.save()
    form = OrganizationDeleteForm(data, instance=organization, user=staff_user)
    assert not form.is_valid()
