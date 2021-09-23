from dataclasses import dataclass
from typing import Optional


@dataclass
class SendgridConfiguration:
    api_key: Optional[str]
    sender_name: Optional[str]
    sender_address: Optional[str]
    account_confirmation_template_id: Optional[str]
    account_set_customer_password_template_id: Optional[str]
    account_delete_template_id: Optional[str]
    account_change_email_confirm_template_id: Optional[str]
    account_change_email_request_template_id: Optional[str]
    account_password_reset_template_id: Optional[str]
    invoice_ready_template_id: Optional[str]
    order_confirmation_template_id: Optional[str]
    order_confirmed_template_id: Optional[str]
    order_fulfillment_confirmation_template_id: Optional[str]
    order_fulfillment_update_template_id: Optional[str]
    order_payment_confirmation_template_id: Optional[str]
    order_canceled_template_id: Optional[str]
    order_refund_confirmation_template_id: Optional[str]
    send_gift_card_template_id: Optional[str]
