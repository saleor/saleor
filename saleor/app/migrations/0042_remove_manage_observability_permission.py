from django.db import migrations


def remove_manage_observability_permission(apps, _schema_editor):
    """Revoke MANAGE_OBSERVABILITY from every user, group, app and app extension.

    The permission row itself is left in place, the same way `manage_apps` was
    handled in 0039. Migration 0014 recreates it on fresh databases via a
    post-migrate hook, so deleting the row here would only make the outcome
    depend on hook ordering, and a stale row nothing can be granted from is
    harmless.
    """
    Permission = apps.get_model("permission", "Permission")
    App = apps.get_model("app", "App")
    AppExtension = apps.get_model("app", "AppExtension")
    Group = apps.get_model("account", "Group")
    User = apps.get_model("account", "User")

    permission = Permission.objects.filter(
        codename="manage_observability", content_type__app_label="app"
    ).first()
    if permission is None:
        return

    App.permissions.through.objects.filter(permission=permission).delete()
    AppExtension.permissions.through.objects.filter(permission=permission).delete()
    Group.permissions.through.objects.filter(permission=permission).delete()
    User.user_permissions.through.objects.filter(permission=permission).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0041_merge_20260714_1040"),
        ("account", "0072_group"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="app",
            options={
                "ordering": ("name", "pk"),
                "permissions": (("manage_apps", "Manage apps"),),
            },
        ),
        migrations.RunPython(
            remove_manage_observability_permission, migrations.RunPython.noop
        ),
    ]
