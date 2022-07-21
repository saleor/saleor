from collections import defaultdict
from typing import Union

from django.contrib.auth.hashers import check_password

from saleor.app.models import App, AppToken
from saleor.graphql.core.dataloaders import DataLoader


def get_app(raw_auth_token) -> Union[None, App]:
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
        for key in keys:
            last_4s_map[key[-4:]].append(key)

        tokens = (
            AppToken.objects.using(self.database_connection_name)
            .filter(token_last_4__in=last_4s_map.keys())
            .values_list("auth_token", "token_last_4", "app_id")
        )
        app_ids = set()
        for auth_token, token_last_4, app_id in tokens:
            for raw_token in last_4s_map[token_last_4]:
                if check_password(raw_token, auth_token):
                    app_ids.add(app_id)
        apps = App.objects.using(self.database_connection_name).filter(
            id__in=app_ids, is_active=True
        )

        return list(apps)
