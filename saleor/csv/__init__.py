class ExportEvents:
    """The different csv events types."""

    DATA_EXPORT_PENDING = "data_export_pending"
    DATA_EXPORT_SUCCESS = "data_export_success"
    DATA_EXPORT_FAILED = "data_export_failed"
    DATA_EXPORT_DELETED = "data_export_deleted"
    EXPORTED_FILE_SENT = "exported_file_sent"

    CHOICES = [
        (DATA_EXPORT_PENDING, "Data export was started."),
        (DATA_EXPORT_SUCCESS, "Data export was completed successfully."),
        (DATA_EXPORT_FAILED, "Data export failed."),
        (DATA_EXPORT_DELETED, "Export file was started."),
        (
            EXPORTED_FILE_SENT,
            "Email with link to download csv file was sent to the customer.",
        ),
    ]
