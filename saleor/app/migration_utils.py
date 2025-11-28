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


def fill_settings_json(apps, schema_editor):
    AppExtension = apps.get_model("app", "AppExtension")

    # Preserve filled settings, only migrate if empty (fill them)
    qs = AppExtension.objects.filter(settings__exact={}).only(
        "target", "http_target_method", "settings"
    )

    for chunk in queryset_in_batches(qs):
        app_extensions = chunk

        for extension in app_extensions:
            if extension.target.upper() == "WIDGET":
                extension.settings = {
                    "widgetTarget": {"method": extension.http_target_method}
                }

            if extension.target.upper() == "NEW_TAB":
                extension.settings = {
                    "newTabTarget": {"method": extension.http_target_method}
                }

        AppExtension.objects.bulk_update(app_extensions, fields=["settings"])
