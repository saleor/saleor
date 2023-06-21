import pytest

from .....csv import ExportEvents
from .....csv.models import ExportEvent, ExportFile


@pytest.fixture
def export_file_with_events(app, customer_user):
    export_events = []

    export_file = ExportFile.objects.create(
        user=customer_user,
        app=app,
        content_file="test file content",
    )

    for x in range(10):
        export_events.append(
            ExportEvent(
                type=ExportEvents.EXPORT_FAILED,
                parameters={"message": "Export failed."},
                export_file=export_file,
                user=customer_user,
                app=app,
            )
        )

    return ExportEvent.objects.bulk_create(export_events)
