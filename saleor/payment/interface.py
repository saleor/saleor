from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class CreditCardInfo:
    """Uniform way to represent Credit Card information."""

    last_4: str
    exp_year: int
    exp_month: int
    brand: Optional[str] = None
    name_on_card: Optional[str] = None


@dataclass
class GatewayResponse:
    """Dataclass for storing gateway response.

    Used for unifying the representation of gateway response.
    It is required to communicate between Saleor and given payment gateway.
    """

    is_success: bool
    action_required: bool
    kind: str  # use "TransactionKind" class
    amount: Decimal
    currency: str
    transaction_id: Optional[str]
    error: Optional[str]
    customer_id: Optional[str] = None
    card_info: Optional[CreditCardInfo] = None
    raw_response: Optional[Dict[str, str]] = None


@dataclass
class AddressData:
    first_name: str
    last_name: str
    company_name: str
    street_address_1: str
    street_address_2: str
    city: str
    city_area: str
    postal_code: str
    country: str
    country_area: str
    phone: str


@dataclass
class PaymentData:
    """Dataclass for storing all payment information.

    Used for unifying the representation of data.
    It is required to communicate between Saleor and given payment gateway.
    """

    amount: Decimal
    currency: str
    billing: Optional[AddressData]
    shipping: Optional[AddressData]
    order_id: Optional[int]
    customer_ip_address: Optional[str]
    customer_email: str
    token: Optional[str] = None
    customer_id: Optional[str] = None
    reuse_source: bool = False


@dataclass
class TokenConfig:
    """Dataclass for payment gateway token fetching customization."""

    customer_id: Optional[str] = None


@dataclass
class GatewayConfig:
    """Dataclass for storing gateway config data.

    Used for unifying the representation of config data.
    It is required to communicate between Saleor and given payment gateway.
    """

    gateway_name: str
    auto_capture: bool
    # Each gateway has different connection data so we are not able to create
    # a unified structure
    connection_params: Dict[str, Any]
    store_customer: bool = False
    require_3d_secure: bool = False


@dataclass
class CustomerSource:
    """Dataclass for storing information about stored payment sources in gateways."""

    id: str
    gateway: str
    credit_card_info: Optional[CreditCardInfo] = None
