from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..checkout.models import Checkout
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
        self,
        currency: Optional[str] = None,
        checkout: Optional["Checkout"] = None,
        channel_slug: Optional[str] = None,
        active_only: bool = True,
    ) -> List["PaymentGateway"]:
        pass

    @abstractmethod
    def authorize_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def capture_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def refund_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def void_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def confirm_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def token_is_required_as_payment_input(
        self, gateway: str, channel_slug: str
    ) -> bool:
        pass

    @abstractmethod
    def process_payment(
        self, gateway: str, payment_information: "PaymentData", channel_slug: str
    ) -> "GatewayResponse":
        pass

    @abstractmethod
    def get_client_token(
        self, gateway: str, token_config: "TokenConfig", channel_slug: str
    ) -> str:
        pass

    @abstractmethod
    def list_payment_sources(
        self, gateway: str, customer_id: str, channel_slug: str
    ) -> List["CustomerSource"]:
        pass
