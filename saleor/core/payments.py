from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from saleor.payment.interface import PaymentData, GatewayResponse, TokenConfig


class Gateway(Enum):
    """Possible gateway values.

    TODO: Create this in runtime based on available plugins
    """

    DUMMY = "dummy"
    BRAINTREE = "braintree"
    RAZORPAY = "razorpay"
    STRIPE = "stripe"


class PaymentInterface(ABC):
    @abstractmethod
    def list_payment_gateways(self) -> List[Gateway]:
        pass

    @abstractmethod
    def authorize_payment(
        self, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def capture_payment(
        self, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def refund_payment(
        self, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def void_payment(
        self, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def confirm_payment(
        self, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def process_payment(
        self, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def create_payment_form(
        self, data, gateway: Gateway, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def get_client_token(self, gateway: Gateway, token_config: "TokenConfig") -> str:
        pass

    @abstractmethod
    def list_payment_sources(
        self, gateway: Gateway, customer_id: str
    ) -> List["CustomerSource"]:
        pass
