from .address_create import AddressCreate
from .address_delete import AddressDelete
from .address_set_default import AddressSetDefault
from .address_update import AddressUpdate
from .customer_create import CustomerCreate
from .customer_delete import CustomerDelete
from .customer_update import CustomerUpdate
from .staff_create import StaffCreate
from .staff_delete import StaffDelete
from .staff_update import StaffUpdate
from .user_avatar_delete import UserAvatarDelete
from .user_avatar_update import UserAvatarUpdate

__all__ = [
    "AddressCreate",
    "AddressDelete",
    "AddressSetDefault",
    "AddressUpdate",
    "CustomerCreate",
    "CustomerDelete",
    "CustomerUpdate",
    "StaffCreate",
    "StaffDelete",
    "StaffUpdate",
    "UserAvatarDelete",
    "UserAvatarUpdate",
]
