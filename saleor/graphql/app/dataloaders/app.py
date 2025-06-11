import hashlib
from collections import defaultdict
from dataclasses import dataclass

from django.contrib.auth.hashers import check_password
from django.core.cache import cache

from ....app.models import App, AppToken
from ...core.dataloaders import DataLoader

# Cache timeout for the app token loader
CACHE_TIMEOUT = 30 * 60 * 60 * 24  # 30 days


def create_app_cache_key_from_token(token: str) -> str:
    """Create a cache key for the app based on the token."""
    return f"AppByTokenLoader:{hashlib.md5(token.encode('utf-8')).hexdigest()}"


class AppByIdLoader(DataLoader[str, App]):
    context_key = "app_by_id"

    def batch_load(self, keys):
        apps = (
            App.objects.using(self.database_connection_name)
            .filter(removed_at__isnull=True)
            .in_bulk(keys)
        )
        return [apps.get(key) for key in keys]


@dataclass
class TokenInfo:
    raw_token: str
    _cache_key: str | None = None

    @property
    def last_4(self) -> str:
        return self.raw_token[-4:]

    @property
    def cache_key(self) -> str:
        if self._cache_key is None:
            self._cache_key = create_app_cache_key_from_token(self.raw_token)
            return self._cache_key
        return self._cache_key


class AppByTokenLoader(DataLoader[str, App]):
    context_key = "app_by_token"

    def get_and_cache_app_id(
        self, token_info: TokenInfo, token_id: int, auth_token: str, app_id: int
    ):
        """Check if the token is valid and return the app ID."""
        cached_data = cache.get(token_info.cache_key)
        if cached_data:
            cached_app_id, cached_token_id = cached_data
            if token_id == cached_token_id:
                return cached_app_id
        elif check_password(token_info.raw_token, auth_token):
            cache_data = (app_id, token_id)
            cache.set(token_info.cache_key, cache_data, CACHE_TIMEOUT)
            return app_id
        return None

    def remove_not_valid_tokens_from_cache(
        self, last_4s_to_raw_token_map, tokens_found
    ):
        """Remove tokens from the cache that are not valid."""
        for token_infos in last_4s_to_raw_token_map.values():
            for token_info in token_infos:
                if token_info.raw_token not in tokens_found:
                    cache.delete(token_info.cache_key)

    def batch_load(self, keys):
        last_4s_to_raw_token_map = defaultdict(list)

        for raw_token in keys:
            token_info = TokenInfo(raw_token=raw_token)
            last_4s_to_raw_token_map[token_info.last_4].append(token_info)

        # Fetch tokens for keys that are not in the cache and check if they are valid
        authed_apps = {}
        tokens = (
            AppToken.objects.using(self.database_connection_name)
            .filter(token_last_4__in=last_4s_to_raw_token_map.keys())
            .values_list("auth_token", "token_last_4", "app_id", "id")
        )
        tokens_found = set()
        for auth_token, token_last_4, app_id, token_id in tokens:
            for token_info in last_4s_to_raw_token_map[token_last_4]:
                if token_info.raw_token in tokens_found:
                    # Skip if we already checked this token
                    continue
                app_id = self.get_and_cache_app_id(
                    token_info, token_id, auth_token, app_id
                )
                if app_id:
                    authed_apps[token_info.raw_token] = app_id
                    tokens_found.add(token_info.raw_token)

        # Remove the cache for tokens that are not valid
        self.remove_not_valid_tokens_from_cache(last_4s_to_raw_token_map, tokens_found)

        apps = (
            App.objects.using(self.database_connection_name)
            .filter(
                id__in=authed_apps.values(), is_active=True, removed_at__isnull=True
            )
            .in_bulk()
        )
        return [apps.get(authed_apps.get(key)) for key in keys]


class ActiveAppByIdLoader(DataLoader):
    context_key = "active_app_by_id"

    def batch_load(self, keys):
        apps_map = (
            App.objects.using(self.database_connection_name)
            .filter(is_active=True, removed_at__isnull=True)
            .prefetch_related("permissions__content_type")
            .in_bulk()
        )
        return [apps_map.get(app_id) for app_id in keys]
