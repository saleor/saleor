import json

from django.urls import reverse

from saleor.account.models import CustomerNote, User
from saleor.dashboard.customer.forms import (
    CustomerDeleteForm, CustomerForm, CustomerNoteForm)


def test_ajax_users_list(admin_client, admin_user, customer_user):
    users = sorted([admin_user, customer_user], key=lambda user: user.email)
    users_list = [
        {'id': user.pk, 'text': user.get_ajax_label()} for user in users]

    url = reverse('dashboard:ajax-users-list')
    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 200
    assert resp_decoded == {'results': users_list}


def test_customers_list(admin_client):
    response = admin_client.get(reverse('dashboard:customers'))
    assert response.status_code == 200


def test_customer_detail_view(admin_client, customer_user):
    response = admin_client.get(
        reverse('dashboard:customer-details', args=[customer_user.pk]))
    assert response.status_code == 200


def test_customer_create(admin_client):
    response = admin_client.get(reverse('dashboard:customer-create'))
    assert response.status_code == 200


def test_customer_create_post(admin_client):
    url = reverse('dashboard:customer-create')
    response = admin_client.post(url, data={'email': 'customer01@example.com'})
    assert response.status_code == 302
    assert User.objects.filter(email='customer01@example.com').exists()


def test_add_customer_form():
    user_count = User.objects.count()
    customer_form = CustomerForm({'email': 'customer01@example.com'})
    customer_form.is_valid()
    customer_form.save()
    assert User.objects.count() == user_count + 1


def test_edit_customer_names(customer_user):
    customer = customer_user
    customer_form = CustomerForm(
        {'first_name': 'Jan', 'last_name': 'Nowak', 'email': customer.email},
        instance=customer)
    customer_form.is_valid()
    customer_form.save()
    updated_user = User.objects.get(pk=customer_user.pk)
    assert updated_user.first_name == 'Jan'
    assert updated_user.last_name == 'Nowak'


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


def test_view_delete_customer(admin_client, admin_user, customer_user):
    url = reverse('dashboard:customer-delete', args=[admin_user.pk])
    response = admin_client.post(url, data={'csrf': 'exampledata'})
    assert response.status_code == 400

    url = reverse('dashboard:customer-delete', args=[customer_user.pk])
    response = admin_client.get(url)
    assert response.status_code == 200

    response = admin_client.post(url, data={'csrf': 'exampledata'})
    assert not User.objects.filter(pk=customer_user.pk).exists()
    assert response.status_code == 302


def test_form_delete_customer(
        staff_user, customer_user, admin_user, permission_manage_staff):
    data = {'csrf': 'example-data'}
    form = CustomerDeleteForm(data, instance=customer_user, user=staff_user)
    assert form.is_valid()

    # Deleting your own account is not allowed
    form = CustomerDeleteForm(data, instance=staff_user, user=staff_user)
    assert not form.is_valid()

    # Deleting a superuser is not allowed
    form = CustomerDeleteForm(data, instance=admin_user, user=staff_user)
    assert not form.is_valid()

    # Deleting another staff is not allowed without relevant permission
    another_staff_user = User.objects.create(is_staff=True, email='exa@mp.le')
    form = CustomerDeleteForm(
        data, instance=another_staff_user, user=staff_user)
    assert not form.is_valid()

    staff_user.user_permissions.add(permission_manage_staff)
    staff_user = User.objects.get(pk=staff_user.pk)
    form = CustomerDeleteForm({}, instance=another_staff_user, user=staff_user)
    assert form.is_valid()
