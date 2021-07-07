from collections import defaultdict

from ...account.models import Address, CustomerEvent, User
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


class CustomerEventsByUserLoader(DataLoader):
    context_key = "customer_events_by_user"

    def batch_load(self, keys):
        events = CustomerEvent.objects.filter(user_id__in=keys)
        events_by_user_map = defaultdict(list)
        for event in events:
            events_by_user_map[event.user_id].append(event)
        return [events_by_user_map.get(user_id, []) for user_id in keys]
