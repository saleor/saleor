from collections import defaultdict

import jwt
from django.contrib.auth.models import Permission

from ...account.models import Address, CustomerEvent, User
from ...core.auth import get_token_from_request
from ...core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_THIRDPARTY_ACCESS_TYPE,
    PERMISSIONS_FIELD,
    is_saleor_token,
    jwt_decode,
)
from ...core.permissions import (
    get_permissions_from_codenames,
    get_permissions_from_names,
)
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


def load_user_from_request(request):
    if request is None:
        return None
    jwt_token = get_token_from_request(request)
    if not jwt_token or not is_saleor_token(jwt_token):
        return None
    payload = jwt_decode(jwt_token)

    jwt_type = payload.get("type")
    if jwt_type not in [JWT_ACCESS_TYPE, JWT_THIRDPARTY_ACCESS_TYPE]:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    permissions = payload.get(PERMISSIONS_FIELD, None)

    user = UserByEmailLoader(request).load(payload["email"]).get()
    user_jwt_token = payload.get("token")
    if not user_jwt_token or not user:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    if user.jwt_token_key != user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )

    if permissions is not None:
        token_permissions = get_permissions_from_names(permissions)
        token_codenames = [perm.codename for perm in token_permissions]
        user.effective_permissions = get_permissions_from_codenames(token_codenames)
        user.is_staff = True if user.effective_permissions else False

    if payload.get("is_staff"):
        user.is_staff = True
    return user
