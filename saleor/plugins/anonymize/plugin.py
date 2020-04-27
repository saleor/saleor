from typing import TYPE_CHECKING, Any, Optional

from ..base_plugin import BasePlugin
from . import obfuscate_address, obfuscate_email, obfuscate_order

if TYPE_CHECKING:
    from ...account.models import Address, User
    from ...order.models import Order


class AnonymizePlugin(BasePlugin):
    """Anonymize all user data in the checkout, user profile and its orders."""

    PLUGIN_NAME = "Anonymize"
    PLUGIN_ID = "mirumee.anonymize"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "Anonymize customer's personal data in the checkout, such as shipping "
        "or billing address, email and phone number."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def change_user_address(
        self,
        address: "Address",
        address_type: Optional[str],
        user: Optional["User"],
        previous_value: "Address",
    ) -> "Address":
        if address.phone:
            address.phone = ""  # type: ignore
        address = obfuscate_address(address)
        address.save()
        return address

    def order_created(self, order: "Order", previous_value: Any):
        order = obfuscate_order(order)
        order.save()

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        customer.email = obfuscate_email(customer.email)
        customer.save()
