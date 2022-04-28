import django.db.models.deletion
from django.db import migrations, models
from django.db.models.signals import post_migrate

import saleor.core.utils.json_serializer


def update_groups_with_manage_pages_with_new_permission(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        Group = apps.get_model("auth", "Group")
        Permission = apps.get_model("auth", "Permission")
        ContentType = apps.get_model("contenttypes", "ContentType")

        ct, _ = ContentType.objects.get_or_create(app_label="page", model="pagetype")
        manage_page_types_and_attributes_perm, _ = Permission.objects.get_or_create(
            codename="manage_page_types_and_attributes",
            content_type=ct,
            name="Manage page types and attributes.",
        )

        groups = Group.objects.filter(
            permissions__content_type__app_label="page",
            permissions__codename="manage_pages",
        )
        for group in groups:
            group.permissions.add(manage_page_types_and_attributes_perm)

    post_migrate.connect(on_migrations_complete, weak=False)


def add_page_types_to_existing_pages(apps, schema_editor):
    Page = apps.get_model("page", "Page")
    PageType = apps.get_model("page", "PageType")

    pages = Page.objects.all()

    if pages:
        page_type = PageType.objects.create(name="Default", slug="default")

        page_type.pages.add(*pages)


class Migration(migrations.Migration):

    dependencies = [
        ("page", "0016_auto_20201112_0904"),
    ]

    operations = [
        migrations.CreateModel(
            name="PageType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "private_metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                ("name", models.CharField(max_length=250)),
                (
                    "slug",
                    models.SlugField(allow_unicode=True, max_length=255, unique=True),
                ),
            ],
            options={
                "ordering": ("slug",),
                "permissions": (
                    (
                        "manage_page_types_and_attributes",
                        "Manage page types and attributes.",
                    ),
                ),
            },
        ),
        migrations.RunPython(
            update_groups_with_manage_pages_with_new_permission,
            migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="page",
            name="page_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pages",
                to="page.pagetype",
            ),
        ),
        migrations.RunPython(
            add_page_types_to_existing_pages, migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="page",
            name="page_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pages",
                to="page.pagetype",
            ),
        ),
    ]
