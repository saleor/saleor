from collections import defaultdict
from collections.abc import Iterable
from typing import Generic, TypeVar, cast

from ...account.models import Address, CustomerEvent, Group, User
from ...attribute.models.base import Attribute, AttributeValue
from ...attribute.models.user import AssignedUserAttributeValue
from ...channel.models import Channel
from ...permission.models import Permission
from ...thumbnail.models import Thumbnail
from ...thumbnail.utils import get_thumbnail_format
from ..attribute.dataloaders import (
    AttributesBySlugLoader,
    AttributeValueByIdLoader,
    AttributeValuesByAttributeIdLoader,
)
from ..core.dataloaders import DataLoader


class AddressByIdLoader(DataLoader[int, Address]):
    context_key = "address_by_id"

    def batch_load(self, keys):
        address_map = Address.objects.using(self.database_connection_name).in_bulk(keys)
        return [address_map.get(address_id) for address_id in keys]


class UserByUserIdLoader(DataLoader[str, User]):
    context_key = "user_by_id"

    def batch_load(self, keys):
        user_map = User.objects.using(self.database_connection_name).in_bulk(keys)
        return [user_map.get(user_id) for user_id in keys]


class CustomerEventsByUserLoader(DataLoader[str, list[CustomerEvent]]):
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
    DataLoader[tuple[int, int, str | None], Thumbnail]
):
    context_key = "thumbnail_by_user_size_and_format"

    def batch_load(self, keys: Iterable[tuple[int, int, str | None]]):
        user_ids = [user_id for user_id, _, _ in keys]
        thumbnails = Thumbnail.objects.using(self.database_connection_name).filter(
            user_id__in=user_ids
        )
        thumbnails_by_user_size_and_format_map: defaultdict[
            tuple[int, int, str | None], Thumbnail | None
        ] = defaultdict()
        for thumbnail in thumbnails:
            format = get_thumbnail_format(thumbnail.format)
            thumbnails_by_user_size_and_format_map[
                (cast(int, thumbnail.user_id), thumbnail.size, format)
            ] = thumbnail
        return [thumbnails_by_user_size_and_format_map.get(key) for key in keys]


class UserByEmailLoader(DataLoader[str, User]):
    context_key = "user_by_email"

    def batch_load(self, keys):
        user_map = (
            User.objects.using(self.database_connection_name)
            .filter(is_active=True)
            .in_bulk(keys, field_name="email")
        )
        return [user_map.get(email) for email in keys]


class PermissionByCodenameLoader(DataLoader[str, Permission]):
    context_key = "permission_by_codename"

    def batch_load(self, keys):
        permission_map = (
            Permission.objects.filter(codename__in=keys)
            .prefetch_related("content_type")
            .in_bulk(field_name="codename")
        )
        return [permission_map.get(codename) for codename in keys]


K = TypeVar("K")


class BaseAccessibleChannels(DataLoader[K, list[Channel]], Generic[K]):
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


class AccessibleChannelsByGroupIdLoader(BaseAccessibleChannels[int]):
    context_key = "accessiblechannels_by_group"

    def batch_load(self, keys):
        group_to_channels = self.get_group_to_channels_map(keys)
        return [group_to_channels.get(group_id, []) for group_id in keys]


class AccessibleChannelsByUserIdLoader(BaseAccessibleChannels[str]):
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


class RestrictedChannelAccessByUserIdLoader(DataLoader[int, bool]):
    context_key = "restrictedchannelaccess_by_user"

    def batch_load(self, keys):
        UserGroup = User.groups.through
        user_groups = UserGroup._default_manager.using(
            self.database_connection_name
        ).filter(user_id__in=keys)
        groups = Group.objects.using(self.database_connection_name).filter(
            id__in=user_groups.values("group_id")
        )

        group_id_to_restricted_access = dict(
            groups.values_list("id", "restricted_access_to_channels")
        )

        user_to_restricted_access: defaultdict[int, bool] = defaultdict(lambda: True)
        for user_id, group_id in user_groups.values_list("user_id", "group_id"):
            user_to_restricted_access[user_id] &= group_id_to_restricted_access[
                group_id
            ]

        return [user_to_restricted_access[user_id] for user_id in keys]


class AssignedUserAttributeValueByUserIdLoader(
    DataLoader[int, list[AssignedUserAttributeValue]]
):
    context_key = "assigneduserattributevalue_by_user_id"

    def batch_load(self, keys):
        user_attribute_values = AssignedUserAttributeValue.objects.using(
            self.database_connection_name
        ).filter(user_id__in=keys)
        response_map = defaultdict(list)
        for assigned_attr_value in user_attribute_values:
            response_map[assigned_attr_value.user_id].append(assigned_attr_value)
        return [response_map.get(user_id, []) for user_id in keys]


class SelectedAttributesAllByUserIdLoader(DataLoader[int, list[dict]]):
    context_key = "selectedattributes_all_by_user_id"

    def batch_load(self, keys):
        def with_assigned_attr_values(
            user_attribute_values: list[list[AssignedUserAttributeValue]],
        ):
            user_id_to_attr_value_ids = defaultdict(list)
            value_ids = []
            for assigned_attr_values in user_attribute_values:
                for assigned_attr_value in assigned_attr_values:
                    if not assigned_attr_value:
                        continue
                    user_id_to_attr_value_ids[assigned_attr_value.user_id].append(
                        assigned_attr_value.value_id
                    )
                    value_ids.append(assigned_attr_value.value_id)

            def with_atr_values(attr_values: list[AttributeValue]):
                # FIXME: If we will decide to keep list instead of pagination, then this
                # should be changed to dataloader
                attr_value_map = {
                    attr_value.id: attr_value for attr_value in attr_values
                }
                attributes_map = (
                    Attribute.objects.using(self.database_connection_name)
                    .filter(
                        id__in=[attr_value.attribute_id for attr_value in attr_values]
                    )
                    .in_bulk()
                )
                response_map = defaultdict(list)
                for (
                    user_id,
                    selected_attr_value_ids,
                ) in user_id_to_attr_value_ids.items():
                    user_selected_attr_id_to_values = defaultdict(list)
                    for selected_attr_value_id in selected_attr_value_ids:
                        selected_attr_value = attr_value_map.get(selected_attr_value_id)
                        if not selected_attr_value:
                            continue
                        user_selected_attr_id_to_values[
                            selected_attr_value.attribute_id
                        ].append(selected_attr_value)

                    for attr_id, attr_values in user_selected_attr_id_to_values.items():
                        response_map[user_id].append(
                            {
                                "attribute": attributes_map[attr_id],
                                "values": attr_values,
                            }
                        )

                return [response_map[user_id] for user_id in keys]

            return (
                AttributeValueByIdLoader(self.context)
                .load_many(value_ids)
                .then(with_atr_values)
            )

        return (
            AssignedUserAttributeValueByUserIdLoader(self.context)
            .load_many(keys)
            .then(with_assigned_attr_values)
        )


class SelectedAttributesVisibleInStorefrontByUserIdLoader(DataLoader[int, list[dict]]):
    context_key = "selectedattributes_visible_in_storefront_by_user_id"

    def batch_load(self, keys):
        def with_all_attributes(attributes):
            response_map = defaultdict(list)
            for user_id, user_details in zip(keys, attributes, strict=False):
                for attr_data in user_details:
                    if attr_data["attribute"].visible_in_storefront:
                        response_map[user_id].append(attr_data)

            return [response_map.get(user_id) for user_id in keys]

        return (
            SelectedAttributesAllByUserIdLoader(self.context)
            .load_many(keys)
            .then(with_all_attributes)
        )


class SelectedAttributeByUserIdAttributeSlugLoader(DataLoader[tuple[int, int], dict]):
    context_key = "selectedattribute_by_user_id_attribute_slug"

    def batch_load(self, keys):
        attribute_slugs = [attr_slug for _, attr_slug in keys]
        user_ids = [user_id for user_id, _ in keys]

        def with_attributes(attributes: list[Attribute]):
            attribute_slugs_map = {attr.slug: attr for attr in attributes if attr}
            attribute_ids = [attr.id for attr in attributes if attr]

            def with_attribute_values(attribute_values: list[list[AttributeValue]]):
                attribute_to_values_map = defaultdict(list)
                attribute_value_ids = []
                for attribute_id, attr_values in zip(
                    attribute_ids, attribute_values, strict=False
                ):
                    attribute_to_values_map[attribute_id] = attr_values
                    if attr_values:
                        attribute_value_ids.extend(attr_values)

                assigned_attribute_values = AssignedUserAttributeValue.objects.using(
                    self.database_connection_name
                ).filter(user_id__in=user_ids, value_id__in=attribute_value_ids)
                assigned_values_per_user = defaultdict(list)
                for assigned_attr_value in assigned_attribute_values:
                    assigned_values_per_user[assigned_attr_value.user_id].append(
                        assigned_attr_value.value_id
                    )
                response_map = {}
                for user_id, attr_slug in keys:
                    attribute = attribute_slugs_map.get(attr_slug)
                    if not attribute:
                        continue
                    assigned_values = [
                        value
                        for value in attribute_to_values_map[attribute.id]
                        if value.id in assigned_values_per_user[user_id]
                    ]
                    response_map[(user_id, attr_slug)] = {
                        "attribute": attribute,
                        "values": assigned_values,
                    }
                return [response_map.get(key) for key in keys]

            return (
                AttributeValuesByAttributeIdLoader(self.context)
                .load_many(attribute_ids)
                .then(with_attribute_values)
            )

        return (
            AttributesBySlugLoader(self.context)
            .load_many(attribute_slugs)
            .then(with_attributes)
        )


class SelectedAttributeVisibleInStorefrontByUserIdAttributeSlugLoader(
    DataLoader[tuple[int, int], dict]
):
    context_key = "selectedattribute_visible_in_storefront_by_user_id_attribute_slug"

    def batch_load(self, keys):
        def with_all_attributes(selected_attributes):
            response_map = {}
            user_ids = [user_id for user_id, _ in keys]
            for user_id, selected_details in zip(
                user_ids, selected_attributes, strict=False
            ):
                if not selected_details:
                    continue
                attribute = selected_details["attribute"]
                if attribute.visible_in_storefront:
                    response_map[(user_id, attribute.slug)] = selected_details
            return [response_map.get(key) for key in keys]

        return (
            SelectedAttributeByUserIdAttributeSlugLoader(self.context)
            .load_many(keys)
            .then(with_all_attributes)
        )
