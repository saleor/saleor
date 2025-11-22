from saleor.app.types import AppExtensionTarget

BATCH_SIZE = 100


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.order_by("pk").filter(pk__gt=start_pk)[:BATCH_SIZE]
        qs_list = list(qs)

        if not qs_list:
            break

        yield qs_list

        start_pk = qs_list[-1].pk


def migrate_target_enum_upper_string(apps, schema_editor):
    AppExtension = apps.get_model("app", "AppExtension")

    qs = AppExtension.objects.all().only("target")

    for chunk in queryset_in_batches(qs):
        app_extensions = chunk

        for extension in app_extensions:
            extension.target = extension.target.upper()

        AppExtension.objects.bulk_update(app_extensions, fields=["target"])


def migrate_mount_enum_upper_string(apps, schema_editor):
    AppExtension = apps.get_model("app", "AppExtension")

    qs = AppExtension.objects.all().only("mount")

    for chunk in queryset_in_batches(qs):
        app_extensions = chunk

        for extension in app_extensions:
            extension.mount = extension.mount.upper()

        AppExtension.objects.bulk_update(app_extensions, fields=["mount"])


def fill_settings_json(apps, schema_editor):
    AppExtension = apps.get_model("app", "AppExtension")

    # Preserve filled settings, only migrate if empty (fill them)
    qs = AppExtension.objects.filter(settings__exact={}).only(
        "target", "http_target_method", "settings"
    )

    for chunk in queryset_in_batches(qs):
        app_extensions = chunk

        for extension in app_extensions:
            if extension.target.upper() == AppExtensionTarget.WIDGET.upper():
                extension.settings = {
                    "widgetTarget": {"method": extension.http_target_method}
                }

            if extension.target.upper() == AppExtensionTarget.NEW_TAB.upper():
                extension.settings = {
                    "newTabTarget": {"method": extension.http_target_method}
                }

        AppExtension.objects.bulk_update(app_extensions, fields=["settings"])
