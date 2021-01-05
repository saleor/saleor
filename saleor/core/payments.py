from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    # flake8: noqa
    from ..checkout.models import Checkout, CheckoutLine
    from ..discount import DiscountInfo
    from ..payment.interface import (
        CustomerSource,
        GatewayResponse,
        PaymentData,
        PaymentGateway,
        TokenConfig,
    )


class PaymentInterface(ABC):
    @abstractmethod
    def list_payment_gateways(
        self, currency: Optional[str] = None, active_only: bool = True
    ) -> List["PaymentGateway"]:
        pass

    @abstractmethod
    def checkout_available_payment_gateways(
        self,
        checkout: "Checkout",
    ) -> List["PaymentGateway"]:
        pass

    @abstractmethod
    def authorize_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def capture_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def refund_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def void_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def confirm_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def token_is_required_as_payment_input(self, gateway) -> bool:
        pass

    @abstractmethod
    def process_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def get_client_token(self, gateway: str, token_config: "TokenConfig") -> str:
        pass

    @abstractmethod
    def list_payment_sources(
        self, gateway: str, customer_id: str
    ) -> List["CustomerSource"]:
        pass
