from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from saleor.payment.interface import PaymentData, GatewayResponse, CustomerSource


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
    def list_payment_sources(self, customer_id: str) -> List["CustomerSource"]:
        pass
