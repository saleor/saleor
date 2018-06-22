from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from saleor.account.models import User
from saleor.core.utils import build_absolute_uri
from saleor.dashboard.staff.forms import StaffForm
from saleor.settings import DEFAULT_FROM_EMAIL


def test_staff_form_not_valid(db):
    data = {'groups': 1}
    form = StaffForm(data=data)
    assert not form.is_valid()


def test_staff_form_create_valid(
        admin_client, staff_user, staff_group):
    assert staff_user.groups.count() == 0
    url = reverse('dashboard:staff-details', kwargs={'pk': staff_user.pk})
    data = {'email': 'staff@example.com', 'groups': staff_group.pk}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.groups.count() == 1


def test_staff_form_create_not_valid(admin_client, staff_user):
    url = reverse('dashboard:staff-details', kwargs={'pk': staff_user.pk})
    data = {'groups': 1}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.groups.count() == 0


def test_admin_cant_change_his_permissions(admin_client, admin_user):
    assert admin_user.is_active
    assert admin_user.is_staff

    url = reverse('dashboard:staff-details', kwargs={'pk': admin_user.pk})
    data = {'is_active': False, 'is_staff': False}
    response = admin_client.post(url, data)
    admin_user = User.objects.get(pk=admin_user.pk)

    assert response.status_code == 200
    assert admin_user.is_active
    assert admin_user.is_staff


def test_delete_staff(admin_client, staff_user):
    user_count = User.objects.all().count()
    url = reverse('dashboard:staff-delete', kwargs={'pk': staff_user.pk})
    data = {'pk': staff_user.pk}
    response = admin_client.post(url, data)
    assert User.objects.all().count() == user_count - 1
    assert response['Location'] == reverse('dashboard:staff-list')


def test_delete_staff_no_post(admin_client, staff_user):
    user_count = User.objects.all().count()
    url = reverse('dashboard:staff-delete', kwargs={'pk': staff_user.pk})
    admin_client.get(url)
    assert User.objects.all().count() == user_count


def test_delete_staff_with_orders(admin_client, staff_user, order):
    order.user = staff_user
    order.save()
    user_count = User.objects.all().count()
    url = reverse('dashboard:staff-delete', kwargs={'pk': staff_user.pk})
    data = {'pk': staff_user.pk}
    response = admin_client.post(url, data)

    # Staff placed some orders in the past, so his acc should be not deleted
    assert User.objects.all().count() == user_count
    staff_user.refresh_from_db()
    # Instead, his privileges are taken away
    assert not staff_user.is_staff
    assert response['Location'] == reverse('dashboard:staff-list')


def test_staff_create_email_with_set_link_password(
        admin_client, staff_group):
    user_count = User.objects.count()
    mail_outbox_count = len(mail.outbox)
    url = reverse('dashboard:staff-create')
    data = {
        'email': 'staff3@example.com', 'groups': staff_group.pk,
        'is_staff': True}
    response = admin_client.post(url, data)

    assert User.objects.count() == user_count + 1
    assert len(mail.outbox) == mail_outbox_count + 1
    assert response['Location'] == reverse('dashboard:staff-list')


def test_send_set_password_email(staff_user, site_settings):
    site = site_settings.site
    ctx = {
        'protocol': 'http',
        'domain': site.domain,
        'site_name': site.name,
        'uid': urlsafe_base64_encode(force_bytes(staff_user.pk)).decode(),
        'token': default_token_generator.make_token(staff_user)}
    send_templated_mail(
        template_name='dashboard/staff/set_password',
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[staff_user.email],
        context=ctx)
    assert len(mail.outbox) == 1
    generated_link = reverse(
        'account:reset-password-confirm',
        kwargs={'uidb64': ctx['uid'], 'token': ctx['token']})
    absolute_generated_link = build_absolute_uri(generated_link)
    sended_message = mail.outbox[0].body
    assert absolute_generated_link in sended_message


def test_create_staff_and_set_password(admin_client, staff_group):
    url = reverse('dashboard:staff-create')
    data = {
        'email': 'staff3@example.com', 'groups': staff_group.pk,
        'is_staff': True}
    response = admin_client.post(url, data)
    assert response.status_code == 302
    new_user = User.objects.get(email='staff3@example.com')
    assert not new_user.has_usable_password()
    uid = urlsafe_base64_encode(force_bytes(new_user.pk)).decode()
    token = default_token_generator.make_token(new_user)
    response = admin_client.get(
        reverse(
            'account:reset-password-confirm',
            kwargs={'uidb64': uid, 'token': token}))
    assert response.status_code == 302
    post_data = {'new_password1': 'password', 'new_password2': 'password'}
    response = admin_client.post(response['Location'], post_data)
    assert response.status_code == 302
    assert response['Location'] == reverse('account:reset-password-complete')
    new_user = User.objects.get(email='staff3@example.com')
    assert new_user.has_usable_password()


def test_create_staff_from_customer(admin_client, staff_group, customer_user):
    url = reverse('dashboard:staff-create')
    data = {'email': customer_user.email, 'groups': staff_group.pk}
    admin_client.post(url, data)
    customer_user.refresh_from_db()
    assert customer_user.is_staff
