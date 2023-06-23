import pytest

from .....csv import ExportEvents
from .....csv.models import ExportEvent, ExportFile


@pytest.fixture
def export_file_with_events(app, customer_user):
    export_file = ExportFile.objects.create(
        user=customer_user,
        app=app,
        content_file="test file content",
    )

    export_events = [
        ExportEvent(
            type=ExportEvents.EXPORT_FAILED,
            parameters={"message": "Export failed."},
            export_file=export_file,
            user=customer_user,
            app=app,
        )
        for _ in range(10)
    ]

    return ExportEvent.objects.bulk_create(export_events)
