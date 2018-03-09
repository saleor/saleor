from unittest import mock

import pytest
from django.conf import settings
from django.urls import reverse

import saleor.order.emails as emails
from saleor.core.utils import build_absolute_uri


def test_get_email_context(order, site_settings):
    site = site_settings.site
    order_url = build_absolute_uri(
        reverse('order:details', kwargs={'token': order.token}))
    proper_context = {
        'protocol': 'https' if settings.ENABLE_SSL else 'http',
        'site_name': site.name,
        'domain': site.domain,
        'url': order_url}

    received_context = emails.get_email_context(order.token)
    assert proper_context == received_context


def test_collect_data_for_order_confirmation_email(order):
    """Order confirmation email requires extra data, which should be present
    in email's context.
    """
    template = emails.CONFIRM_ORDER_TEMPLATE
    email_data = emails.collect_data_for_email(order.pk, template)
    email_context = email_data['context']
    assert email_context['order'] == order
    assert 'schema_markup' in email_context


def test_collect_data_for_email(order):
    template = emails.CONFIRM_PAYMENT_TEMPLATE
    email_data = emails.collect_data_for_email(order.pk, template)
    email_context = email_data['context']
    # Those properties should be present only for order confirmation email
    assert 'order' not in email_context
    assert 'schema_markup' not in email_context


@pytest.mark.parametrize('send_email,template', [
    (emails.send_payment_confirmation, emails.CONFIRM_PAYMENT_TEMPLATE),
    (emails.send_note_confirmation, emails.CONFIRM_NOTE_TEMPLATE),
    (emails.send_order_confirmation, emails.CONFIRM_ORDER_TEMPLATE)])
@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_emails(mocked_templated_email, order, template, send_email):
    send_email(order.pk)
    email_data = emails.collect_data_for_email(order.pk, template)
    email_context = email_data['context']
    mocked_templated_email.assert_called_once_with(
        recipient_list=[order.get_user_current_email()],
        context=email_context,
        from_email=settings.ORDER_FROM_EMAIL,
        template_name=template)
