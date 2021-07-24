from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class Address(BaseModel):
    type: str
    id: str
    first_name: str
    last_name: str
    company_name: Optional[str]
    street_address_1: str
    street_address_2: Optional[str]
    city: str
    city_area: Optional[str]
    postal_code: str
    country: str
    country_area: Optional[str]
    phone: Optional[str]


class Customer(BaseModel):
    type: str
    id: str
    default_shipping_address: Optional[Address]
    default_billing_address: Optional[Address]
    addresses: List[Address]
    private_metadata: Dict[str, Any]
    metadata: Dict[str, Any]
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    date_joined: str

    class Config:
        extra = "forbid"


class CustomerCreated(Customer):
    ...


class CustomerUpdated(Customer):
    ...


class WebhookSchema(BaseModel):
    __root__: List[Union[CustomerCreated, CustomerUpdated]]
