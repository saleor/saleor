from django.contrib.postgres.indexes import BTreeIndex
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("product", "0195_add_slug_to_translations"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="categorytranslation",
            index=BTreeIndex(
                fields=["language_code", "slug"], name="categorytranslation_slug_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="collectiontranslation",
            index=BTreeIndex(
                fields=["language_code", "slug"], name="collectiontranslation_slug_idx"
            ),
        ),
        AddIndexConcurrently(
            model_name="producttranslation",
            index=BTreeIndex(
                fields=["language_code", "slug"], name="producttranslation_slug_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="categorytranslation",
            constraint=models.UniqueConstraint(
                fields=("language_code", "slug"), name="categorytranslation_slug_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="collectiontranslation",
            constraint=models.UniqueConstraint(
                fields=("language_code", "slug"),
                name="collectiontranslation_slug_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="producttranslation",
            constraint=models.UniqueConstraint(
                fields=("language_code", "slug"), name="producttranslation_slug_unique"
            ),
        ),
    ]
