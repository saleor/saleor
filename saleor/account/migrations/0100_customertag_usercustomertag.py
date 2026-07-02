import django.contrib.postgres.indexes
import django.db.models.deletion
from django.db import migrations, models

import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0099_remove_digitalcontent_customerevent_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerTag",
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
                        db_default={},
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        db_default={},
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "slug",
                    models.SlugField(allow_unicode=True, max_length=255, unique=True),
                ),
                ("description", models.TextField(blank=True, default="")),
                (
                    "is_public",
                    models.BooleanField(db_default=False, default=False),
                ),
            ],
            options={
                "ordering": ("name", "pk"),
                "permissions": (
                    ("manage_customer_tags", "Manage customer tags."),
                    ("assign_customer_tags", "Assign customer tags to users."),
                ),
                "abstract": False,
                "indexes": [
                    django.contrib.postgres.indexes.GinIndex(
                        fields=["private_metadata"], name="customertag_p_meta_idx"
                    ),
                    django.contrib.postgres.indexes.GinIndex(
                        fields=["metadata"], name="customertag_meta_idx"
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="UserCustomerTag",
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
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="account.user",
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_assignments",
                        to="account.customertag",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customer_tag_assignments",
                        to="account.user",
                    ),
                ),
            ],
            options={
                "ordering": ("pk",),
            },
        ),
        migrations.AddField(
            model_name="user",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="users",
                through="account.UserCustomerTag",
                through_fields=("user", "tag"),
                to="account.customertag",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="usercustomertag",
            unique_together={("user", "tag")},
        ),
    ]
