from ...account.models import Address, User
from ..core.dataloaders import DataLoader


class AddressByIdLoader(DataLoader):
    context_key = "address_by_id"

    def batch_load(self, keys):
        address_map = Address.objects.in_bulk(keys)
        return [address_map.get(address_id) for address_id in keys]


class UserByUserIdLoader(DataLoader):
    context_key = "user_by_id"

    def batch_load(self, keys):
        user_map = User.objects.in_bulk(keys)
        return [user_map.get(user_id) for user_id in keys]
