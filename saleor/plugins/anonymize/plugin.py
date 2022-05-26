from typing import TYPE_CHECKING, Any, Optional

from django.utils import timezone
from django.utils.crypto import get_random_string
from faker import Faker

from ...account import search
from ...core.anonymize import obfuscate_address
from ...order.search import prepare_order_search_document_value
from ..base_plugin import BasePlugin
from . import obfuscate_order

if TYPE_CHECKING:
    from ...account.models import Address, User
    from ...order.models import Order

faker = Faker()


class AnonymizePlugin(BasePlugin):
    """Anonymize all user data in the checkout, user profile and its orders."""

    PLUGIN_NAME = "Anonymize"
    PLUGIN_ID = "mirumee.anonymize"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "Anonymize customer's personal data in the checkout, such as shipping "
        "or billing address, email and phone number."
    )
    CONFIGURATION_PER_CHANNEL = False

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
        order.search_document = prepare_order_search_document_value(order)
        order.save()

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        customer.first_name = faker.first_name()
        customer.last_name = faker.last_name()
        timestamp = str(timezone.now())
        email = f"{hash(timestamp + get_random_string(5))}@anonymous-demo-email.com"
        customer.email = email
        customer.search_document = search.prepare_user_search_document_value(
            customer, attach_addresses_data=False
        )
        customer.save()
