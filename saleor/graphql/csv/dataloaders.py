from collections import defaultdict

from ...csv.models import ExportEvent
from ..core.dataloaders import DataLoader


class EventsByExportFileIdLoader(DataLoader):
    context_key = "events_by_export_file_id"

    def batch_load(self, keys):
        events = ExportEvent.objects.using(self.database_connection_name).filter(
            export_file_id__in=keys
        )
        return self.events_by_export_file_id(events, keys)

    def events_by_export_file_id(self, events, keys):
        events_map = defaultdict(list)
        for event in events:
            events_map[event.export_file_id].append(event)
        return [events_map.get(export_file_id) for export_file_id in keys]
