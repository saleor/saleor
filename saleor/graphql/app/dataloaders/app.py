from collections import defaultdict

from django.contrib.auth.hashers import check_password

from ....app.models import App, AppToken
from ...core.dataloaders import DataLoader


class AppByIdLoader(DataLoader[str, App]):
    context_key = "app_by_id"

    def batch_load(self, keys):
        apps = (
            App.objects.using(self.database_connection_name)
            .filter(removed_at__isnull=True)
            .in_bulk(keys)
        )
        return [apps.get(key) for key in keys]


class AppByTokenLoader(DataLoader[str, App]):
    context_key = "app_by_token"

    def batch_load(self, keys):
        last_4s_to_raw_token_map = defaultdict(list)
        for raw_token in keys:
            last_4s_to_raw_token_map[raw_token[-4:]].append(raw_token)

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
            .filter(
                id__in=authed_apps.values(), is_active=True, removed_at__isnull=True
            )
            .in_bulk()
        )

        return [apps.get(authed_apps.get(key)) for key in keys]
