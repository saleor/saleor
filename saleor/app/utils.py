from typing import Union

from django.contrib.auth.hashers import check_password

from saleor.app.models import App, AppToken


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
