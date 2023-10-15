from collections import defaultdict
from functools import partial, wraps
from typing import Optional

from django.contrib.auth.hashers import check_password
from django.utils.functional import LazyObject
from promise import Promise

from ...app.models import App, AppExtension, AppToken
from ...core.auth import get_token_from_request
from ...core.utils.lazyobjects import unwrap_lazy
from ..core import SaleorContext
from ..core.dataloaders import BaseThumbnailBySizeAndFormatLoader, DataLoader


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


class AppsByAppIdentifierLoader(DataLoader):
    context_key = "apps_by_app_identifier"

    def batch_load(self, keys):
        apps = App.objects.using(self.database_connection_name).filter(
            identifier__in=keys
        )
        apps_map = defaultdict(list)
        for app in apps:
            apps_map[app.identifier].append(app)
        return [apps_map.get(app_identifier, []) for app_identifier in keys]


class AppTokensByAppIdLoader(DataLoader):
    context_key = "app_tokens_by_app_id"

    def batch_load(self, keys):
        tokens = AppToken.objects.using(self.database_connection_name).filter(
            app_id__in=keys
        )
        tokens_by_app_map = defaultdict(list)
        for token in tokens:
            tokens_by_app_map[token.app_id].append(token)
        return [tokens_by_app_map.get(app_id, []) for app_id in keys]


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
        tokens = (
            AppToken.objects.using(self.database_connection_name)
            .filter(token_last_4__in=last_4s_to_raw_token_map.keys())
            .values_list("auth_token", "token_last_4", "app_id")
        )
        authed_apps = {}
        for auth_token, token_last_4, app_id in tokens:
            for raw_token in last_4s_to_raw_token_map[token_last_4]:
                if check_password(raw_token, auth_token):
                    authed_apps[raw_token] = app_id

        apps = (
            App.objects.using(self.database_connection_name)
            .filter(id__in=authed_apps.values(), is_active=True)
            .in_bulk()
        )

        return [apps.get(authed_apps.get(key)) for key in keys]


class ThumbnailByAppIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_app_size_and_format"
    model_name = "app"


class ThumbnailByAppInstallationIdSizeAndFormatLoader(
    BaseThumbnailBySizeAndFormatLoader
):
    context_key = "thumbnail_by_app_installation_size_and_format"
    model_name = "app_installation"


def promise_app(context: SaleorContext) -> Promise[Optional[App]]:
    auth_token = get_token_from_request(context)
    if not auth_token or len(auth_token) != 30:
        return Promise.resolve(None)
    return AppByTokenLoader(context).load(auth_token)


def get_app_promise(context: SaleorContext) -> Promise[Optional[App]]:
    if hasattr(context, "app"):
        app = context.app
        if isinstance(app, LazyObject):
            app = unwrap_lazy(app)
        return Promise.resolve(app)

    return promise_app(context)


def app_promise_callback(func):
    @wraps(func)
    def _wrapper(root, info, *args, **kwargs):
        return get_app_promise(info.context).then(
            partial(func, root, info, *args, **kwargs)
        )

    return _wrapper
