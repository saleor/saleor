from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate


def update_groups_with_manage_users_with_new_permission(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        try:
            apps = kwargs["apps"]
        except KeyError:
            # In test when we use use `@pytest.mark.django_db(transaction=True)`
            # pytest trigger additional post_migrate signal without `apps` in kwargs.
            return
        Group = apps.get_model("account", "Group")
        Permission = apps.get_model("permission", "Permission")
        ContentType = apps.get_model("contenttypes", "ContentType")

        ct, _ = ContentType.objects.get_or_create(
            app_label="account", model="customertype"
        )
        manage_customer_types_and_attributes_perm, _ = Permission.objects.get_or_create(
            codename="manage_customer_types_and_attributes",
            content_type=ct,
            name="Manage customer types and attributes.",
        )

        groups = Group.objects.filter(
            permissions__content_type__app_label="account",
            permissions__codename="manage_users",
        )
        for group in groups.iterator():
            group.permissions.add(manage_customer_types_and_attributes_perm)

    sender = registry.get_app_config("account")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0104_assign_default_customer_type_to_users"),
    ]

    operations = [
        migrations.RunPython(
            update_groups_with_manage_users_with_new_permission,
            migrations.RunPython.noop,
        ),
    ]
