from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from saleor.payment.interface import PaymentData, GatewayResponse, TokenConfig


class PaymentInterface(ABC):
    @abstractmethod
    def list_payment_gateways(self, active_only: bool) -> List[str]:
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
    def process_payment(
        self, gateway: str, payment_information: "PaymentData"
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def create_payment_form(
        self, data, gateway: str, payment_information: "PaymentData"
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

    @abstractmethod
    def get_payment_template(self, gateway: str) -> str:
        pass
