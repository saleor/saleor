from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    # flake8: noqa
    from saleor.payment.interface import (
        PaymentData,
        GatewayResponse,
        TokenConfig,
        CustomerSource,
    )


class PaymentInterface(ABC):
    @abstractmethod
    def list_payment_gateways(
        self, currency: Optional[str] = None, active_only: bool = True
    ) -> List[dict]:
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
    def get_client_token(self, gateway: str, token_config: "TokenConfig") -> str:
        pass

    @abstractmethod
    def list_payment_sources(
        self, gateway: str, customer_id: str
    ) -> List["CustomerSource"]:
        pass
