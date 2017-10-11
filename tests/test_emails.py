from __future__ import unicode_literals

import saleor.order.emails as emails
import pytest
import mock


EMAIL_DATA = {'from_email': 'foo@bar.com',
              'template_name': emails.CONFIRMATION_TEMPLATE}


@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_confirmation_using_templated_email(mocked_templated_email):
    emails.send_confirmation(EMAIL_DATA['from_email'])
    mocked_templated_email.assert_called_once_with(recipient_list=[],
                                                   context={},
                                                   **EMAIL_DATA)
