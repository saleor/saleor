from django.contrib.auth.hashers import check_password
from django.db.models import Exists, OuterRef

from saleor.app.models import App, AppToken
from saleor.graphql.core.dataloaders import SingleObjectLoader


class AppByTokenLoader(SingleObjectLoader):
    context_key = "app_by_token"

    def batch_load(self, keys):
        raw_auth_token = list(keys)[0]
        tokens = AppToken.objects.filter(token_last_4=raw_auth_token[-4:]).values_list(
            "id", "auth_token"
        )
        token_ids = [
            id
            for id, auth_token in tokens
            if check_password(raw_auth_token, auth_token)
        ]
        return [
            App.objects.filter(
                Exists(tokens.filter(id__in=token_ids, app_id=OuterRef("pk"))),
                is_active=True,
            ).first()
        ]
