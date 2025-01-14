from collections import defaultdict

from ...core import SaleorContext
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from ..subscription_payload import initialize_request


class PayloadsRequestContextByEventTypeLoader(DataLoader):
    context_key = "payloads_request_context_by_event_type"

    def batch_load(self, keys):
        request_context_by_event_type: dict[str, SaleorContext | None] = defaultdict()
        requestor = get_user_or_app_from_context(self.context)
        for event_type in keys:
            request_context_by_event_type[event_type] = initialize_request(
                requestor,
                sync_event=True,
                allow_replica=False,
                event_type=event_type,
            )
        return [request_context_by_event_type.get(event_type) for event_type in keys]
