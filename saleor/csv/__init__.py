class ExportEvents:
    """The different csv events types."""

    EXPORT_PENDING = "export_pending"
    EXPORT_SUCCESS = "export_success"
    EXPORT_FAILED = "export_failed"
    EXPORT_DELETED = "export_deleted"
    EXPORTED_FILE_SENT = "exported_file_sent"
    EXPORT_FAILED_INFO_SENT = "Export_failed_info_sent"

    CHOICES = [
        (EXPORT_PENDING, "Data export was started."),
        (EXPORT_SUCCESS, "Data export was completed successfully."),
        (EXPORT_FAILED, "Data export failed."),
        (EXPORT_DELETED, "Export file was deleted."),
        (
            EXPORTED_FILE_SENT,
            "Email with link to download file was sent to the customer.",
        ),
        (
            EXPORT_FAILED_INFO_SENT,
            "Email with info that export failed was sent to the customer.",
        ),
    ]


class FileTypes:
    CSV = "csv"
    XLSX = "xlsx"

    CHOICES = [
        (CSV, "Plain CSV file."),
        (XLSX, "Excel XLSX file."),
    ]
