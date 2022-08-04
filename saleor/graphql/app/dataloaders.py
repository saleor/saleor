from collections import defaultdict
from typing import Union

from django.contrib.auth.hashers import check_password

from ...app.models import App, AppExtension, AppToken
from ..core.dataloaders import DataLoader


class AppByIdLoader(DataLoader):
    context_key = "app_by_id"

    def batch_load(self, keys):
        apps = App.objects.using(self.database_connection_name).in_bulk(keys)
        return [apps.get(key) for key in keys]


class AppExtensionByIdLoader(DataLoader):
    context_key = "app_extension_by_id"

    def batch_load(self, keys):
        extensions = AppExtension.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [extensions.get(key) for key in keys]


class AppExtensionByAppIdLoader(DataLoader):
    context_key = "app_extension_by_app_id"

    def batch_load(self, keys):
        extensions = AppExtension.objects.using(self.database_connection_name).filter(
            app_id__in=keys
        )
        extensions_map = defaultdict(list)
        app_extension_loader = AppExtensionByIdLoader(self.context)
        for extension in extensions.iterator():
            extensions_map[extension.app_id].append(extension)
            app_extension_loader.prime(extension.id, extension)
        return [extensions_map.get(app_id, []) for app_id in keys]


def get_app(raw_auth_token) -> Union[None, App]:
    if raw_auth_token is None:
        return None
    tokens = AppToken.objects.filter(token_last_4=raw_auth_token[-4:]).values_list(
        "app_id", "auth_token"
    )
    app_ids = [
        app_id
        for app_id, auth_token in tokens
        if check_password(raw_auth_token, auth_token)
    ]
    return App.objects.filter(id__in=app_ids, is_active=True).first()


class AppByTokenLoader(DataLoader):
    context_key = "app_by_token"

    def batch_load(self, keys):
        last_4s_map = defaultdict(list)
        for raw_token in keys:
            last_4s_map[raw_token[-4:]].append(raw_token)

        tokens = (
            AppToken.objects.using(self.database_connection_name)
            .filter(token_last_4__in=last_4s_map.keys())
            .values_list("auth_token", "token_last_4", "app_id")
        )
        authed_apps = {}
        for auth_token, token_last_4, app_id in tokens:
            for raw_token in last_4s_map[token_last_4]:
                if check_password(raw_token, auth_token):
                    authed_apps[raw_token] = app_id

        apps = App.objects.using(self.database_connection_name).filter(
            id__in=authed_apps.values(), is_active=True
        )

        return [apps.filter(id=authed_apps.get(key, None)).first() for key in keys]
