from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("page", "0028_add_default_page_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="pagetranslation",
            name="slug",
            field=models.SlugField(allow_unicode=True, max_length=255, null=True),
        ),
        AddIndexConcurrently(
            model_name="pagetranslation",
            index=BTreeIndex(
                fields=["language_code", "slug"], name="pagetranslation_slug_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="pagetranslation",
            constraint=models.UniqueConstraint(
                fields=["language_code", "slug"], name="pagetranslation_slug_unique"
            ),
        ),
    ]
