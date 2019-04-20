from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.templatetags.static import static
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from saleor.account.models import User
from saleor.core.utils import build_absolute_uri
from saleor.dashboard.staff.forms import StaffForm
from saleor.dashboard.staff.utils import remove_staff_member
from saleor.settings import DEFAULT_FROM_EMAIL


def test_remove_staff_member_with_orders(
        staff_user, permission_manage_products, order):
    order.user = staff_user
    order.save()
    staff_user.user_permissions.add(permission_manage_products)

    remove_staff_member(staff_user)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert not staff_user.is_staff
    assert not staff_user.user_permissions.exists()


def test_remove_staff_member(staff_user):
    remove_staff_member(staff_user)
    assert not User.objects.filter(pk=staff_user.pk).exists()


def test_staff_form_not_valid(staff_user):
    data = {'user_permissions': 1}
    form = StaffForm(data=data, user=staff_user)
    assert not form.is_valid()


def test_staff_form_create_valid(
        admin_client, staff_user, permission_manage_products):
    assert staff_user.user_permissions.count() == 0
    url = reverse('dashboard:staff-details', kwargs={'pk': staff_user.pk})
    data = {
        'email': 'staff@example.com', 'is_staff': True,
        'user_permissions': permission_manage_products.pk}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.user_permissions.count() == 1


def test_staff_form_create_not_valid(admin_client, staff_user):
    url = reverse('dashboard:staff-details', kwargs={'pk': staff_user.pk})
    data = {'csrf': 'examplecsfr'}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.user_permissions.count() == 0


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


def test_staff_form_remove_permissions_after_unassign_is_staff(
        admin_client, staff_user, permission_manage_products):
    staff_user.user_permissions.add(permission_manage_products)
    assert staff_user.is_active
    assert staff_user.is_staff
    assert staff_user.user_permissions.count() == 1

    url = reverse('dashboard:staff-details', kwargs={'pk': staff_user.pk})
    data = {
        'email': staff_user.email, 'is_active': True, 'is_staff': False,
        'user_permissions': permission_manage_products.pk}
    response = admin_client.post(url, data)

    staff_user.refresh_from_db()
    assert response.status_code == 302
    assert staff_user.is_active
    assert not staff_user.is_staff
    assert staff_user.user_permissions.count() == 0


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


def test_staff_create_email_with_set_link_password(admin_client):
    user_count = User.objects.count()
    mail_outbox_count = len(mail.outbox)
    url = reverse('dashboard:staff-create')
    data = {'email': 'staff3@example.com', 'is_staff': True}
    response = admin_client.post(url, data)

    assert User.objects.count() == user_count + 1
    assert len(mail.outbox) == mail_outbox_count + 1
    assert response['Location'] == reverse('dashboard:staff-list')


def test_send_set_password_email(staff_user, site_settings):
    site = site_settings.site
    uid = urlsafe_base64_encode(force_bytes(staff_user.pk))
    token = default_token_generator.make_token(staff_user)
    logo_url = build_absolute_uri(static('images/logo-light.svg'))
    password_set_url = build_absolute_uri(
        reverse(
            'account:reset-password-confirm',
            kwargs={'token': token, 'uidb64': uid}))
    ctx = {
        'logo_url': logo_url,
        'password_set_url': password_set_url,
        'site_name': site.name}
    send_templated_mail(
        template_name='dashboard/staff/set_password',
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=[staff_user.email],
        context=ctx)
    assert len(mail.outbox) == 1
    generated_link = reverse(
        'account:reset-password-confirm',
        kwargs={
            'uidb64': uid,
            'token': token})
    absolute_generated_link = build_absolute_uri(generated_link)
    sended_message = mail.outbox[0].body
    assert absolute_generated_link in sended_message


def test_create_staff_and_set_password(admin_client):
    url = reverse('dashboard:staff-create')
    data = {
        'first_name': 'Jan', 'last_name': 'Nowak',
        'email': 'staff3@example.com', 'is_staff': True}
    response = admin_client.post(url, data)
    assert response.status_code == 302
    new_user = User.objects.get(email='staff3@example.com')
    assert new_user.first_name == 'Jan'
    assert new_user.last_name == 'Nowak'
    assert not new_user.password
    uid = urlsafe_base64_encode(force_bytes(new_user.pk))
    token = default_token_generator.make_token(new_user)
    response = admin_client.get(
        reverse(
            'account:reset-password-confirm',
            kwargs={
                'uidb64': uid,
                'token': token}))
    assert response.status_code == 302
    post_data = {'new_password1': 'password', 'new_password2': 'password'}
    response = admin_client.post(response['Location'], post_data)
    assert response.status_code == 302
    assert response['Location'] == reverse('account:reset-password-complete')
    new_user = User.objects.get(email='staff3@example.com')
    assert new_user.has_usable_password()


def test_create_staff_from_customer(
        admin_client, customer_user, permission_manage_products):
    url = reverse('dashboard:staff-create')
    data = {
        'email': customer_user.email, 'is_staff': True,
        'user_permissions': permission_manage_products.pk}
    admin_client.post(url, data)
    customer_user.refresh_from_db()
    assert customer_user.is_staff
