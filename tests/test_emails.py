from unittest import mock

import pytest
from django.conf import settings

import saleor.order.emails as emails

EMAIL = "foo@bar.com"
DOMAIN = 'mirumee.com'
SITE_NAME = 'mirumee.com'
URL = 'wooba/looba'
EMAIL_FROM = settings.ORDER_FROM_EMAIL


@pytest.mark.parametrize('fun,template,update_context', [
    (emails.send_order_confirmation, emails.CONFIRM_ORDER_TEMPLATE, True),
    (emails.send_payment_confirmation, emails.CONFIRM_PAYMENT_TEMPLATE, False),
    (emails.send_note_confirmation, emails.CONFIRM_NOTE_TEMPLATE, False)])
@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_emails(
        mocked_templated_email, update_context, order, template, fun):
    with mock.patch('saleor.order.emails.collect_data_for_email',
                    return_value={
                        'email': EMAIL,
                        'url': URL,
                        'template': template}):
        fun(order.pk)
        context = {
            'protocol': 'http',
            'domain': DOMAIN,
            'site_name': SITE_NAME,
            'url': URL}
        if update_context:
            context.update({'order': order})
        mocked_templated_email.assert_called_once_with(
            recipient_list=[EMAIL],
            context=context,
            from_email=EMAIL_FROM,
            template_name=template)
