from ...account.models import Address
from ..core.dataloaders import DataLoader


class AddressByIdLoader(DataLoader):
    context_key = "address_by_id"

    def batch_load(self, keys):
        address_map = Address.objects.in_bulk(keys)
        return [address_map.get(address_id) for address_id in keys]
