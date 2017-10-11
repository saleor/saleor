from __future__ import unicode_literals
from django.conf import settings

import saleor.order.emails as emails
import pytest
import mock


EMAIL_DATA = {'from_email': settings.ORDER_FROM_EMAIL,
              'template_name': emails.CONFIRMATION_TEMPLATE}


@mock.patch('saleor.order.emails.get_site_name', return_value='WOOBALOOBA')
@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_confirmation_using_templated_email(mocked_templated_email,
                                                 mocked_get_site_name):
    email_address = 'foo@bar.com'
    url = 'wooba/looba'
    emails.send_confirmation(email_address, url)
    context = {'site_name': mocked_get_site_name(),
               'payment_url': url}
    mocked_templated_email.assert_called_once_with(
        recipient_list=[email_address], context=context, **EMAIL_DATA)
