from collections import defaultdict

from ....app.models import AppToken
from ...core.dataloaders import DataLoader


class AppTokensByAppIdLoader(DataLoader[str, AppToken]):
    context_key = "app_tokens_by_app_id"

    def batch_load(self, keys):
        tokens = AppToken.objects.using(self.database_connection_name).filter(
            app_id__in=keys, app__removed_at__isnull=True
        )
        tokens_by_app_map = defaultdict(list)
        for token in tokens:
            tokens_by_app_map[token.app_id].append(token)
        return [tokens_by_app_map.get(app_id, []) for app_id in keys]
