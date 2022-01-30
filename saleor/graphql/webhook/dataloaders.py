from ...core.models import EventPayload
from ..core.dataloaders import DataLoader


class PayloadByIdLoader(DataLoader):
    context_key = "payload_by_id"

    def batch_load(self, keys):
        payload = EventPayload.objects.using(self.database_connection_name).in_bulk(
            keys
        )
        return [payload.get(payload_id).payload for payload_id in keys]
