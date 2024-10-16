import datetime

from django.db import migrations


def set_missing_product_publication_date(apps, schema_editor):
    Product = apps.get_model("product", "Product")
    published_product = Product.objects.filter(
        publication_date__isnull=True, is_published=True
    )
    published_product.update(
        publication_date=datetime.datetime.now(tz=datetime.UTC).date()
    )


def set_missing_collection_publication_date(apps, schema_editor):
    Collection = apps.get_model("product", "Collection")
    published_collection = Collection.objects.filter(
        publication_date__isnull=True, is_published=True
    )
    published_collection.update(
        publication_date=datetime.datetime.now(tz=datetime.UTC).date()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0127_auto_20201001_0933"),
    ]

    operations = [
        migrations.RunPython(set_missing_product_publication_date),
        migrations.RunPython(set_missing_collection_publication_date),
    ]
