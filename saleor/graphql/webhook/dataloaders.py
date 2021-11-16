from saleor.core.models import EventDeliveryAttempt
from saleor.graphql.core.dataloaders import DataLoader


class AttemptsByDeliveryLoader(DataLoader):
    context_key = "attempts_by_delivery"

    def batch_load(self, keys):
        attempts = EventDeliveryAttempt.objects.in_bulk(keys)
        return [attempts.get(attempt=attempt) for attempt in keys]
