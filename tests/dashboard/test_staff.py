from __future__ import unicode_literals

from django.core import mail
from django.core.urlresolvers import reverse

from django.contrib.auth.tokens import default_token_generator
from django.test.client import Client
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from templated_email import send_templated_mail

from saleor.dashboard.staff.forms import StaffForm
from saleor.userprofile.models import User
from saleor.settings import DEFAULT_FROM_EMAIL, get_host
from saleor.site.utils import get_site_name


def test_staff_form_not_valid(db):
    data = {'groups': 1}
    form = StaffForm(data=data)
    assert not form.is_valid()


def test_staff_form_create_valid(
        admin_client, staff_user, staff_group):
    url = reverse('dashboard:staff-details', args=[staff_user.pk])
    data = {'email': 'staff@example.com', 'groups': staff_group.pk}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.groups.count() == 1


def test_staff_create_email_with_set_link_password(
        admin_client, staff_group):
    url = reverse('dashboard:staff-create')
    data = {'email': 'staff3@example.com', 'groups': staff_group.pk,
            'is_staff': True}
    response = admin_client.post(url, data)
    assert User.objects.count() == 2
    assert len(mail.outbox) == 1
    assert response['Location'] == reverse('dashboard:staff-list')


def test_send_set_password_email(staff_user):
    ctx = {'protocol': 'http',
           'domain': get_host(),
           'site_name': get_site_name(),
           'uid': urlsafe_base64_encode(force_bytes(staff_user.pk)),
           'token': default_token_generator.make_token(staff_user)}
    send_templated_mail(template_name='dashboard/staff/set_password',
                        from_email=DEFAULT_FROM_EMAIL,
                        recipient_list=[staff_user.email],
                        context=ctx)
    assert len(mail.outbox) == 1
    generated_link = ('http://%s/account/password/reset/%s/%s/' %
                      (ctx['domain'], ctx['uid'].decode('utf-8'), ctx['token']))
    sended_message = mail.outbox[0].body
    assert generated_link in sended_message


def test_create_staff_and_set_password(admin_client, staff_group):
    url = reverse('dashboard:staff-create')
    data = {'email': 'staff3@example.com', 'groups': staff_group.pk,
            'is_staff': True}
    response = admin_client.post(url, data)
    assert response.status_code == 302
    new_user = User.objects.get(email='staff3@example.com')
    uid = urlsafe_base64_encode(force_bytes(new_user.pk)),
    token = default_token_generator.make_token(new_user)
    response = admin_client.get(reverse('account_reset_password_confirm',
                                kwargs={'uidb64': uid[0], 'token': token}))
    assert response.status_code == 302
    post_data = {'new_password1': 'password', 'new_password2': 'password'}
    response = admin_client.post(response['Location'], post_data)
    assert response.status_code == 302
    assert response['Location'] == reverse('account_reset_password_complete')
    new_user = User.objects.get(email='staff3@example.com')
    assert new_user.has_usable_password()


def test_staff_form_create_not_valid(admin_client, staff_user):
    url = reverse('dashboard:staff-details', args=[staff_user.pk])
    data = {'groups': 1}
    admin_client.post(url, data)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.groups.count() == 0


def test_delete_staff(admin_client, staff_user):
    assert User.objects.all().count() == 2
    url = reverse('dashboard:staff-delete', kwargs={'pk': staff_user.pk})
    data = {'pk': staff_user.pk}
    response = admin_client.post(url, data)
    assert User.objects.all().count() == 1
    assert response['Location'] == '/dashboard/staff/'


def test_delete_staff_no_POST(admin_client, staff_user):
    url = reverse('dashboard:staff-delete', args=[staff_user.pk])
    admin_client.get(url)
    assert User.objects.all().count() == 2
