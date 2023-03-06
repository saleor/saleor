from collections import defaultdict
from typing import DefaultDict, Iterable, Optional, Tuple, cast

from ...account.models import Address, CustomerEvent, User
from ...permission.models import Permission
from ...thumbnail.models import Thumbnail
from ...thumbnail.utils import get_thumbnail_format
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


class ThumbnailByUserIdSizeAndFormatLoader(
    DataLoader[Tuple[int, int, Optional[str]], Thumbnail]
):
    context_key = "thumbnail_by_user_size_and_format"

    def batch_load(self, keys: Iterable[Tuple[int, int, Optional[str]]]):
        user_ids = [user_id for user_id, _, _ in keys]
        thumbnails = Thumbnail.objects.using(self.database_connection_name).filter(
            user_id__in=user_ids
        )
        thumbnails_by_user_size_and_format_map: DefaultDict[
            Tuple[int, int, Optional[str]], Optional[Thumbnail]
        ] = defaultdict()
        for thumbnail in thumbnails:
            format = get_thumbnail_format(thumbnail.format)
            thumbnails_by_user_size_and_format_map[
                (cast(int, thumbnail.user_id), thumbnail.size, format)
            ] = thumbnail
        return [thumbnails_by_user_size_and_format_map.get(key) for key in keys]


class UserByEmailLoader(DataLoader):
    context_key = "user_by_email"

    def batch_load(self, keys):
        user_map = (
            User.objects.using(self.database_connection_name)
            .filter(is_active=True)
            .in_bulk(keys, field_name="email")
        )
        return [user_map.get(email) for email in keys]


class PermissionByCodenameLoader(DataLoader):
    context_key = "permission_by_codename"

    def batch_load(self, keys):
        permission_map = (
            Permission.objects.filter(codename__in=keys)
            .prefetch_related("content_type")
            .in_bulk(field_name="codename")
        )
        return [permission_map.get(codename) for codename in keys]
