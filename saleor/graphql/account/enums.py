from typing import Final

import graphene
from django_countries import countries

from ...account import CustomerEvents
from ...checkout import AddressType
from ...graphql.core.enums import to_enum
from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.types import BaseEnum
from ..core.utils import str_to_enum

AddressTypeEnum: Final[graphene.Enum] = to_enum(
    AddressType, type_name="AddressTypeEnum"
)

CustomerEventsEnum: Final[graphene.Enum] = to_enum(CustomerEvents)
CustomerEventsEnum.doc_category = DOC_CATEGORY_USERS


def __country_code_enum_description(enum):
    if enum is None:
        return (
            "Represents country codes defined by the ISO 3166-1 alpha-2 standard."
            "\n\nThe `EU` value is DEPRECATED and will be removed in Saleor 3.21."
        )
    for code, name in countries:
        if enum.value == code:
            return name
    return None


CountryCodeEnum = graphene.Enum(
    "CountryCode",
    [(str_to_enum(country[0]), country[0]) for country in countries],
    description=__country_code_enum_description,
)


class StaffMemberStatus(BaseEnum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"

    class Meta:
        description = "Represents status of a staff account."
        doc_category = DOC_CATEGORY_USERS

    @property
    def description(self):
        if self == StaffMemberStatus.ACTIVE:
            return "User account has been activated."
        if self == StaffMemberStatus.DEACTIVATED:
            return "User account has not been activated yet."
        return None
