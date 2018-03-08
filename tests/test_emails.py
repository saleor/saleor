from unittest import mock

import pytest
from django.conf import settings

import saleor.order.emails as emails
from saleor.order.emails_helpers import get_order_confirmation_markup


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
