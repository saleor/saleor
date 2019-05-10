import graphene

from ...checkout import AddressType
from ...graphql.core.enums import to_enum

AddressTypeEnum = to_enum(AddressType, type_name="AddressTypeEnum")


class StaffMemberStatus(graphene.Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
