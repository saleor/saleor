from collections import defaultdict

from ...account.models import Address, CustomerEvent, User
from ...thumbnail.models import Thumbnail
from ..core.dataloaders import DataLoader


class AddressByIdLoader(DataLoader):
    context_key = "address_by_id"

    def batch_load(self, keys):
        address_map = Address.objects.using(self.database_connection_name).in_bulk(keys)
        return [address_map.get(address_id) for address_id in keys]


class UserByUserIdLoader(DataLoader):
    context_key = "user_by_id"

    def batch_load(self, keys):
        user_map = User.objects.using(self.database_connection_name).in_bulk(keys)
        return [user_map.get(user_id) for user_id in keys]


class CustomerEventsByUserLoader(DataLoader):
    context_key = "customer_events_by_user"

    def batch_load(self, keys):
        events = CustomerEvent.objects.using(self.database_connection_name).filter(
            user_id__in=keys
        )
        events_by_user_map = defaultdict(list)
        for event in events:
            events_by_user_map[event.user_id].append(event)
        return [events_by_user_map.get(user_id, []) for user_id in keys]


class ThumbnailByUserIdSizeAndFormatLoader(DataLoader):
    context_key = "thumbnail_by_user_size_and_format"

    def batch_load(self, keys):
        user_ids = [user_id for user_id, _, _ in keys]
        thumbnails = Thumbnail.objects.using(self.database_connection_name).filter(
            user_id__in=user_ids
        )
        thumbnails_by_user_size_and_format_map = defaultdict()
        for thumbnail in thumbnails:
            format = thumbnail.format.lower() if thumbnail.format else None
            thumbnails_by_user_size_and_format_map[
                (thumbnail.user_id, thumbnail.size, format)
            ] = thumbnail
        return [thumbnails_by_user_size_and_format_map.get(key) for key in keys]
