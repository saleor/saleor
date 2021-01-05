from decimal import Decimal
from unittest import mock

from templated_email import get_connection

from ...invoice import emails as invoice_emails
from ...invoice.models import Invoice
from ...order import OrderEvents
from ...order import emails as emails
from ..utils import add_variant_to_draft_order


def test_collect_data_for_order_confirmation_email(order):
    """Order confirmation email requires extra data, which should be present
    in email's context.
    """
    template = emails.CONFIRM_ORDER_TEMPLATE
    email_data = emails.collect_data_for_email(order.pk, template)
    email_context = email_data["context"]
    assert email_context["order"] == order
    assert "schema_markup" in email_context


def test_collect_invoice_data_for_email(order):
    number = "01/12/2020/TEST"
    url = "http://www.example.com"
    invoice = Invoice.objects.create(number=number, url=url, order=order)
    email_data = invoice_emails.collect_invoice_data_for_email(
        invoice, "order/send_invoice"
    )
    email_context = email_data["context"]
    assert email_context["number"] == number
    assert email_context["download_url"] == url
    assert email_data["recipient_list"] == [order.user.email]


def test_collect_data_for_fulfillment_email(fulfilled_order):
    template = emails.CONFIRM_FULFILLMENT_TEMPLATE
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment_data = emails.collect_data_for_fulfillment_email(
        fulfilled_order.pk, template, fulfillment.pk
    )
    email_context = fulfillment_data["context"]
    assert email_context["fulfillment"] == fulfillment
    email_data = emails.collect_data_for_email(fulfilled_order.pk, template)
    assert all([key in email_context for key, item in email_data["context"].items()])


def test_collect_data_for_email(order):
    template = emails.CONFIRM_PAYMENT_TEMPLATE
    email_data = emails.collect_data_for_email(order.pk, template)
    email_context = email_data["context"]
    # This properties should be present only for order confirmation email
    assert "schema_markup" not in email_context


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_email_payment_confirmation(mocked_templated_email, order, site_settings):
    template = emails.CONFIRM_PAYMENT_TEMPLATE
    emails.send_payment_confirmation(order.pk)
    email_data = emails.collect_data_for_email(order.pk, template)

    recipients = [order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_staff_emails_without_notification_recipient(
    mocked_templated_email, order, site_settings
):
    emails.send_staff_order_confirmation(order.pk, "http://www.example.com/")
    mocked_templated_email.assert_not_called()


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_staff_emails(
    mocked_templated_email, order, site_settings, staff_notification_recipient
):
    redirect_url = "http://www.example.com/"
    emails.send_staff_order_confirmation(order.pk, redirect_url)
    email_data = emails.collect_staff_order_notification_data(
        order.pk, emails.STAFF_CONFIRM_ORDER_TEMPLATE, redirect_url
    )

    recipients = [staff_notification_recipient.get_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": emails.STAFF_CONFIRM_ORDER_TEMPLATE,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_email_order_confirmation(mocked_templated_email, order, site_settings):
    template = emails.CONFIRM_ORDER_TEMPLATE
    redirect_url = "https://www.example.com"
    emails.send_order_confirmation(order.pk, redirect_url)
    email_data = emails.collect_data_for_email(order.pk, template, redirect_url)

    recipients = [order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_confirmation_emails_without_addresses_for_payment(
    mocked_templated_email, order, site_settings, digital_content
):

    assert not order.lines.count()

    template = emails.CONFIRM_PAYMENT_TEMPLATE
    add_variant_to_draft_order(order, digital_content.product_variant, quantity=1)
    order.shipping_address = None
    order.shipping_method = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "shipping_method", "billing_address"])

    emails.send_payment_confirmation(order.pk)
    email_data = emails.collect_data_for_email(order.pk, template)

    recipients = [order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_confirmation_emails_without_addresses_for_order(
    mocked_templated_email, order, site_settings, digital_content
):

    assert not order.lines.count()

    template = emails.CONFIRM_ORDER_TEMPLATE
    add_variant_to_draft_order(order, digital_content.product_variant, quantity=1)
    order.shipping_address = None
    order.shipping_method = None
    order.billing_address = None
    order.save(update_fields=["shipping_address", "shipping_method", "billing_address"])

    redirect_url = "https://www.example.com"
    emails.send_order_confirmation(order.pk, redirect_url)
    email_data = emails.collect_data_for_email(order.pk, template, redirect_url)

    recipients = [order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_fulfillment_email_confirmation(
    mocked_templated_email, fulfilled_order, site_settings
):
    template = emails.CONFIRM_FULFILLMENT_TEMPLATE
    redirect_url = "http://localhost.pl"
    order = fulfilled_order
    fulfillment = order.fulfillments.first()
    order.redirect_url = redirect_url
    order.save()
    emails.send_fulfillment_confirmation(
        order_pk=fulfilled_order.pk,
        fulfillment_pk=fulfillment.pk,
        redirect_url=redirect_url,
    )

    email_data = emails.collect_data_for_fulfillment_email(
        fulfilled_order.pk, template, fulfillment.pk, redirect_url
    )

    recipients = [fulfilled_order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }
    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_fulfillment_email_update(
    mocked_templated_email, fulfilled_order, site_settings
):
    template = emails.UPDATE_FULFILLMENT_TEMPLATE
    order = fulfilled_order
    fulfillment = order.fulfillments.first()
    emails.send_fulfillment_update(
        order_pk=fulfilled_order.pk, fulfillment_pk=fulfillment.pk
    )

    email_data = emails.collect_data_for_fulfillment_email(
        fulfilled_order.pk, template, fulfillment.pk
    )

    recipients = [fulfilled_order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }
    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_fulfillment_emails_with_tracking_number_as_url(
    mocked_templated_email, fulfilled_order, site_settings
):
    template = emails.UPDATE_FULFILLMENT_TEMPLATE
    fulfillment = fulfilled_order.fulfillments.first()
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    assert fulfillment.is_tracking_number_url
    emails.send_fulfillment_update(
        order_pk=fulfilled_order.pk, fulfillment_pk=fulfillment.pk
    )
    email_data = emails.collect_data_for_fulfillment_email(
        fulfilled_order.pk, template, fulfillment.pk
    )

    recipients = [fulfilled_order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_fulfillment_email_confirmation_with_tracking_number_as_url(
    mocked_templated_email, fulfilled_order, site_settings
):
    template = emails.CONFIRM_FULFILLMENT_TEMPLATE
    redirect_url = "http://localhost.pl"
    order = fulfilled_order
    fulfillment = order.fulfillments.first()
    fulfillment.tracking_number = "https://www.example.com"
    fulfillment.save()
    order.redirect_url = redirect_url
    order.save()

    assert fulfillment.is_tracking_number_url
    emails.send_fulfillment_confirmation(
        order_pk=fulfilled_order.pk, fulfillment_pk=fulfillment.pk, redirect_url=""
    )
    email_data = emails.collect_data_for_fulfillment_email(
        fulfilled_order.pk, template, fulfillment.pk
    )

    recipients = [fulfilled_order.get_customer_email()]

    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_email_order_canceled(mocked_templated_email, order, site_settings):
    # given
    template = emails.ORDER_CANCEl_TEMPLATE

    # when
    emails.send_order_canceled(order.pk)

    # then
    email_data = emails.collect_data_for_email(order.pk, template)
    recipients = [order.get_customer_email()]
    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_templated_mail")
def test_send_email_order_refunded(mocked_templated_email, order, site_settings):
    # given
    template = emails.ORDER_REFUND_TEMPLATE
    amount = order.total.gross.amount

    # when
    emails.send_order_refunded(order.pk, amount, order.currency)

    # then
    email_data = emails.collect_data_for_email(order.pk, template)
    email_data["context"].update({"amount": amount, "currency": order.currency})
    recipients = [order.get_customer_email()]
    expected_call_kwargs = {
        "context": email_data["context"],
        "from_email": site_settings.default_from_email,
        "template_name": template,
    }

    mocked_templated_email.assert_called_once_with(
        recipient_list=recipients, **expected_call_kwargs
    )

    # Render the email to ensure there is no error
    email_connection = get_connection()
    email_connection.get_email_message(to=recipients, **expected_call_kwargs)


@mock.patch("saleor.order.emails.send_order_refunded.delay")
def test_send_order_refunded_confirmation(send_order_refunded_mock, order):
    # when
    emails.send_order_refunded_confirmation(order, order.user, Decimal(5), "USD")

    # then
    send_order_refunded_mock.assert_called_once_with(order.pk, Decimal(5), "USD")

    order_event = order.events.last()
    assert order_event.type == OrderEvents.EMAIL_SENT


@mock.patch("saleor.order.emails.send_order_canceled.delay")
def test_send_order_canceled_confirmation(send_order_canceled_mock, order):
    # when
    emails.send_order_canceled_confirmation(order, order.user)

    # then
    send_order_canceled_mock.assert_called_once_with(order.pk)

    order_event = order.events.last()
    assert order_event.type == OrderEvents.EMAIL_SENT
