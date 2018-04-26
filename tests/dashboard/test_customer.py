from django.urls import reverse

from saleor.account.models import CustomerNote
from saleor.dashboard.customer.forms import CustomerNoteForm


def test_add_note_to_customer(admin_user, customer_user):
    customer = customer_user
    note = CustomerNote(customer=customer, user=admin_user)
    note_form = CustomerNoteForm({'content': 'test_note'}, instance=note)
    note_form.is_valid()
    note_form.save()
    assert customer.notes.first().content == 'test_note'


def test_add_note_to_customer_from_url(admin_client, customer_user):
    customer = customer_user
    assert customer.notes.count() == 0
    data = {'user': admin_client, 'customer': customer, 'content': 'test_note'}
    url = reverse(
        'dashboard:customer-add-note', kwargs={'customer_pk': customer.pk})
    response = admin_client.post(url, data)

    assert response.status_code == 200
