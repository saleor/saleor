class ExportEvents:
    """The different csv events types."""

    EXPORT_PENDING = "export_pending"
    EXPORT_SUCCESS = "export_success"
    EXPORT_FAILED = "export_failed"
    EXPORT_DELETED = "export_deleted"
    EXPORTED_FILE_SENT = "exported_file_sent"

    CHOICES = [
        (EXPORT_PENDING, "Data export was started."),
        (EXPORT_SUCCESS, "Data export was completed successfully."),
        (EXPORT_FAILED, "Data export failed."),
        (EXPORT_DELETED, "Export file was started."),
        (
            EXPORTED_FILE_SENT,
            "Email with link to download csv file was sent to the customer.",
        ),
    ]


class FileTypes:
    CSV = "csv"
    XLSX = "xlsx"

    CHOICES = [
        (CSV, "Plain csv file."),
        (XLSX, "Excel .xlsx file."),
    ]
