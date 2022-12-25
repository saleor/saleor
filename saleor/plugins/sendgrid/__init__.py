from dataclasses import dataclass


@dataclass
class SendgridConfiguration:
    api_key: str | None
    sender_name: str | None
    sender_address: str | None
    account_confirmation_template_id: str | None
    account_set_customer_password_template_id: str | None
    account_delete_template_id: str | None
    account_change_email_confirm_template_id: str | None
    account_change_email_request_template_id: str | None
    account_password_reset_template_id: str | None
    invoice_ready_template_id: str | None
    order_confirmation_template_id: str | None
    order_confirmed_template_id: str | None
    order_fulfillment_confirmation_template_id: str | None
    order_fulfillment_update_template_id: str | None
    order_payment_confirmation_template_id: str | None
    order_canceled_template_id: str | None
    order_refund_confirmation_template_id: str | None
    send_gift_card_template_id: str | None
