from collections import defaultdict
from collections.abc import Iterable
from typing import Optional, cast

from ...account.models import Address, CustomerEvent, Group, User
from ...channel.models import Channel
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
    DataLoader[tuple[int, int, Optional[str]], Thumbnail]
):
    context_key = "thumbnail_by_user_size_and_format"

    def batch_load(self, keys: Iterable[tuple[int, int, Optional[str]]]):
        user_ids = [user_id for user_id, _, _ in keys]
        thumbnails = Thumbnail.objects.using(self.database_connection_name).filter(
            user_id__in=user_ids
        )
        thumbnails_by_user_size_and_format_map: defaultdict[
            tuple[int, int, Optional[str]], Optional[Thumbnail]
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


class BaseAccessibleChannels(DataLoader):
    def get_group_to_channels_map(self, group_ids):
        groups_with_no_channel_restriction = Group.objects.using(
            self.database_connection_name
        ).filter(id__in=group_ids, restricted_access_to_channels=False)
        groups_with_channel_restriction = Group.objects.using(
            self.database_connection_name
        ).filter(id__in=group_ids, restricted_access_to_channels=True)

        group_to_channels: defaultdict[int, list[Channel]] = defaultdict(list)
        if groups_with_channel_restriction:
            group_to_channels = self.get_group_channels(
                groups_with_channel_restriction.values("id"),
                group_to_channels,
            )

        if groups_with_no_channel_restriction:
            channels = list(Channel.objects.using(self.database_connection_name).all())
            for group_id in groups_with_no_channel_restriction.values_list(
                "id", flat=True
            ):
                group_to_channels[group_id] = channels

        return group_to_channels

    def get_group_channels(self, group_ids, group_to_channels):
        GroupChannels = Group.channels.through
        group_channels = GroupChannels.objects.using(
            self.database_connection_name
        ).filter(group_id__in=group_ids)
        channels_in_bulk = Channel.objects.using(self.database_connection_name).in_bulk(
            list(group_channels.values_list("channel_id", flat=True))
        )

        for group_id, channel_id in group_channels.values_list(
            "group_id", "channel_id"
        ):
            group_to_channels[group_id].append(channels_in_bulk[channel_id])

        return group_to_channels


class AccessibleChannelsByGroupIdLoader(BaseAccessibleChannels):
    context_key = "accessiblechannels_by_group"

    def batch_load(self, keys):
        group_to_channels = self.get_group_to_channels_map(keys)
        return [group_to_channels.get(group_id, []) for group_id in keys]


class AccessibleChannelsByUserIdLoader(BaseAccessibleChannels):
    context_key = "accessiblechannels_by_user"

    def batch_load(self, keys):
        UserGroup = User.groups.through
        user_groups = UserGroup._default_manager.using(
            self.database_connection_name
        ).filter(user_id__in=keys)
        groups = Group.objects.using(self.database_connection_name).filter(
            id__in=user_groups.values("group_id")
        )

        group_to_channels = self.get_group_to_channels_map(
            groups.values_list("id", flat=True)
        )

        user_to_channels: defaultdict[int, set[Channel]] = defaultdict(set)
        for user_id, group_id in user_groups.values_list("user_id", "group_id"):
            user_to_channels[user_id].update(group_to_channels[group_id])

        return [list(user_to_channels[user_id]) for user_id in keys]


class RestrictedChannelAccessByUserIdLoader(DataLoader):
    context_key = "restrictedchannelaccess_by_user"

    def batch_load(self, keys):
        UserGroup = User.groups.through
        user_groups = UserGroup._default_manager.using(
            self.database_connection_name
        ).filter(user_id__in=keys)
        groups = Group.objects.using(self.database_connection_name).filter(
            id__in=user_groups.values("group_id")
        )

        group_id_to_restricted_access = {
            group_id: restricted_access
            for group_id, restricted_access in groups.values_list(
                "id", "restricted_access_to_channels"
            )
        }

        user_to_restricted_access: defaultdict[int, bool] = defaultdict(lambda: True)
        for user_id, group_id in user_groups.values_list("user_id", "group_id"):
            user_to_restricted_access[user_id] &= group_id_to_restricted_access[
                group_id
            ]

        return [user_to_restricted_access[user_id] for user_id in keys]
