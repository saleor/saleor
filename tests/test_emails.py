from unittest import mock

import pytest
from django.templatetags.static import static
from templated_email import get_connection

import saleor.order.emails as emails
from saleor.core.emails import get_email_base_context
from saleor.core.utils import build_absolute_uri


def test_get_email_base_context(site_settings):
    site = site_settings.site
    logo_url = build_absolute_uri(static('images/logo-light.svg'))
    proper_context = {
        'domain': site.domain,
        'logo_url': logo_url,
        'site_name': site.name}

    received_context = get_email_base_context()
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


def test_collect_data_for_fullfillment_email(fulfilled_order):
    template = emails.CONFIRM_FULFILLMENT_TEMPLATE
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment_data = emails.collect_data_for_fullfillment_email(
        fulfilled_order.pk, template, fulfillment.pk)
    email_context = fulfillment_data['context']
    assert email_context['fulfillment'] == fulfillment
    email_data = emails.collect_data_for_email(fulfilled_order.pk, template)
    assert all([
        key in email_context
        for key, item in email_data['context'].items()])


def test_collect_data_for_email(order):
    template = emails.CONFIRM_PAYMENT_TEMPLATE
    email_data = emails.collect_data_for_email(order.pk, template)
    email_context = email_data['context']
    # Those properties should be present only for order confirmation email
    assert 'order' not in email_context
    assert 'schema_markup' not in email_context


@pytest.mark.parametrize('send_email,template', [
    (emails.send_payment_confirmation, emails.CONFIRM_PAYMENT_TEMPLATE),
    (emails.send_order_confirmation, emails.CONFIRM_ORDER_TEMPLATE)])
@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_emails(mocked_templated_email, order, template, send_email, settings):
    send_email(order.pk)
    email_data = emails.collect_data_for_email(order.pk, template)

    recipients = [order.get_user_current_email()]

    expected_call_kwargs = {
        'context': email_data['context'],
        'from_email': settings.ORDER_FROM_EMAIL,
        'template_name': template}

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs)

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@pytest.mark.parametrize('send_email,template', [
    (emails.send_fulfillment_confirmation, emails.CONFIRM_FULFILLMENT_TEMPLATE),  # noqa
    (emails.send_fulfillment_update, emails.UPDATE_FULFILLMENT_TEMPLATE)])
@mock.patch('saleor.order.emails.send_templated_mail')
def test_send_fulfillment_emails(
        mocked_templated_email, template, send_email, fulfilled_order,
        settings):
    fulfillment = fulfilled_order.fulfillments.first()
    send_email(order_pk=fulfilled_order.pk, fulfillment_pk=fulfillment.pk)
    email_data = emails.collect_data_for_fullfillment_email(
        fulfilled_order.pk, template, fulfillment.pk)

    recipients = [fulfilled_order.get_user_current_email()]

    expected_call_kwargs = {
        'context': email_data['context'],
        'from_email': settings.ORDER_FROM_EMAIL,
        'template_name': template}

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs)

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)
