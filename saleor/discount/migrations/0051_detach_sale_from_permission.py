from django.apps import apps as global_apps
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.management import create_contenttypes
from django.db import DEFAULT_DB_ALIAS, migrations


def handle_permissions(apps, _schema_editor):
    app_config = apps.get_app_config("discount")
    app_config.models_module = True
    create_permissions(app_config, apps=apps)
    app_config.models_module = None


def create_permissions(
    app_config,
    verbosity=0,
    interactive=True,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    create_contenttypes(
        app_config,
        verbosity=verbosity,
        interactive=interactive,
        using=using,
        apps=apps,
        **kwargs,
    )

    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("permission", "Permission")
    searched_perms = []
    ctypes = set()
    for model in app_config.get_models():
        ctype = ContentType.objects.db_manager(using).get_for_model(
            model, for_concrete_model=False
        )

        ctypes.add(ctype)
        for perm in _get_all_permissions(model._meta):
            searched_perms.append((ctype, perm))
    all_perms = set(
        Permission.objects.using(using)
        .filter(
            content_type__in=ctypes,
        )
        .values_list("content_type", "codename")
    )
    perms = [
        Permission(codename=codename, name=name, content_type=ct)
        for ct, (codename, name) in searched_perms
        if (ct.pk, codename) not in all_perms
    ]
    Permission.objects.using(using).bulk_create(perms)


def _get_all_permissions(opts):  # noqa: D200, D212
    return [*_get_builtin_permissions(opts), *opts.permissions]


def _get_builtin_permissions(opts):  # noqa: D205, D212
    perms = []
    for action in opts.default_permissions:
        perms.append(
            (
                get_permission_codename(action, opts),
                f"Can {action} {opts.verbose_name_raw}",
            )
        )
    return perms


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0050_merge_20231004_1306"),
    ]

    operations = [
        migrations.RunPython(
            handle_permissions, reverse_code=migrations.RunPython.noop
        ),
        migrations.RunSQL(
            """
            update permission_permission
            set content_type_id = (
                select id
                from django_content_type
                where app_label = 'discount' and model='promotion'
            )
            where codename = 'manage_discounts'
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterModelOptions(
                    name="promotion",
                    options={
                        "ordering": ("name", "pk"),
                        "permissions": (
                            ("manage_discounts", "Manage sales and vouchers."),
                        ),
                    },
                ),
            ],
        ),
    ]
