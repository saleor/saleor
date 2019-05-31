from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class GatewayResponse:
    """Dataclass for storing gateway response. Used for unifying the
    representation of gateway response. It is required to communicate between
    Saleor and given payment gateway."""

    is_success: bool
    kind: str
    amount: Decimal
    currency: str
    transaction_id: str
    error: Optional[str]
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
    """Dataclass for storing all payment information. Used for unifying the
    representation of data. It is required to communicate between Saleor and
    given payment gateway."""

    token: str
    amount: Decimal
    currency: str
    billing: Optional[AddressData]
    shipping: Optional[AddressData]
    order_id: Optional[int]
    customer_ip_address: str
    customer_email: str
    customer_id: str
    reuse_source: bool = False


@dataclass
class GatewayConfig:
    """Dataclass for storing gateway config data. Used for unifying the
    representation of config data. It is required to communicate between
    Saleor and given payment gateway."""

    auto_capture: bool
    template_path: str
    # Each gateway has different connection data so we are not able to create
    # a unified structure
    connection_params: Dict[str, Any]
