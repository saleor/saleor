from __future__ import unicode_literals
from django.conf import settings

import saleor.order.emails as emails
import mock

EMAIL = "foo@bar.com"
SITE_NAME = 'mirumee.com'
URL = 'wooba/looba'
EMAIL_FROM = settings.ORDER_FROM_EMAIL


@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_confirmation_using_templated_email(mocked_templated_email):
    emails.send_order_confirmation(EMAIL, URL)
    context = {'site_name': SITE_NAME, 'url': URL}
    mocked_templated_email.assert_called_once_with(
        recipient_list=[EMAIL],
        context=context,
        from_email=EMAIL_FROM,
        template_name=emails.CONFIRM_ORDER_TEMPLATE)


@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_order_payment_confirmation(mocked_templated_email):
    emails.send_payment_confirmation(EMAIL, URL)
    context = {'site_name': SITE_NAME, 'url': URL}
    mocked_templated_email.assert_called_once_with(
        recipient_list=[EMAIL],
        context=context,
        from_email=EMAIL_FROM,
        template_name=emails.CONFIRM_PAYMENT_TEMPLATE)
