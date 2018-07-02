from django.urls import reverse

from saleor.account.models import User
from saleor.dashboard.company.forms import CompanyDeleteForm


def test_view_delete_company(admin_client, authorized_client, company):
    url = reverse('dashboard:company-delete', args=[company.pk])
    data = {'csrf': 'exampledata'}
    response = authorized_client.get(url, data=data)
    assert response.status_code == 302

    response = admin_client.get(url, data=data)
    assert response.status_code == 200


def test_form_delete_company(
        company_factory, customer_user, staff_user, group_factory):
    # Can only delete a company that doesn't have customers, and only with
    # sufficient permissions.
    data = {'csrf': 'example-data'}
    company = company_factory('Lonely Inc.', '123 Somewhere')
    form = CompanyDeleteForm(data, instance=company, user=staff_user)
    assert not form.is_valid()

    group = group_factory('Company Manager', 'edit_company')
    staff_user.groups.add(group)
    staff_user = User.objects.get(pk=staff_user.pk)
    form = CompanyDeleteForm(data, instance=company, user=staff_user)
    assert form.is_valid()

    # Deleting non-empty company not okay even with edit permission
    company = company_factory('Whoobee Inc.', '123 Somewhere')
    customer_user.company = company
    customer_user.save()
    form = CompanyDeleteForm(data, instance=company, user=staff_user)
    assert not form.is_valid()
