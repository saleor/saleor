from django.db import migrations


def remove_manage_apps_permission(apps, _schema_editor):
    Permission = apps.get_model("permission", "Permission")
    App = apps.get_model("app", "App")
    AppExtension = apps.get_model("app", "AppExtension")

    manage_apps = Permission.objects.filter(
        codename="manage_apps", content_type__app_label="app"
    ).first()
    if manage_apps is None:
        return

    App.permissions.through.objects.filter(permission=manage_apps).delete()
    AppExtension.permissions.through.objects.filter(permission=manage_apps).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0038_merge_20260213_1154"),
    ]

    operations = [
        migrations.RunPython(remove_manage_apps_permission, migrations.RunPython.noop),
    ]
