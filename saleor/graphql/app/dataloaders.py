from collections import defaultdict

from django.contrib.auth.hashers import check_password

from ...app.models import App, AppExtension, AppToken
from ...core.auth import get_token_from_request
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


class AppByTokenLoader(DataLoader):
    context_key = "app_by_token"

    def batch_load(self, keys):
        last_4s_to_raw_token_map = defaultdict(list)
        for raw_token in keys:
            last_4s_to_raw_token_map[raw_token[-4:]].append(raw_token)

        # The app should always be taken from the default database.
        # The app is retrieved from the database before the mutation code is reached,
        # in case the replica database is set the app from the replica will be returned.
        # In such case, when in the mutation there is another ask for an app,
        # the cached instance from the replica is returned. Then the error is raised
        # when any object is saved with a reference to this app.
        # Because of that loaders that are used in context shouldn't use
        # the replica database.
        tokens = AppToken.objects.filter(
            token_last_4__in=last_4s_to_raw_token_map.keys()
        ).values_list("auth_token", "token_last_4", "app_id")
        authed_apps = {}
        for auth_token, token_last_4, app_id in tokens:
            for raw_token in last_4s_to_raw_token_map[token_last_4]:
                if check_password(raw_token, auth_token):
                    authed_apps[raw_token] = app_id

        apps = App.objects.filter(id__in=authed_apps.values(), is_active=True).in_bulk()

        return [apps.get(authed_apps.get(key)) for key in keys]


def promise_app(context):
    auth_token = get_token_from_request(context)
    if not auth_token or len(auth_token) != 30:
        return None
    return AppByTokenLoader(context).load(auth_token)


def load_app(context):
    promise = promise_app(context)
    return None if promise is None else promise.get()
