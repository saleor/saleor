from django.db import migrations


class Migration(migrations.Migration):
    """Drop `AppExtension.http_target_method` from the model state, keeping the column.

    The field has been superseded by `AppExtension.settings` since 3.23. The
    column is left in place so pods running the previous release keep finding it
    during a rolling deploy, and so the release can be rolled back; it is dropped
    in a later migration.
    """

    dependencies = [
        ("app", "0042_merge_20260820_0919"),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name="appextension",
            name="http_target_method",
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]
