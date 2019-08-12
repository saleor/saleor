from dataclasses import dataclass

from django.db import migrations
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber


def ensure_attribute_slugs_are_unique_or_fix(apps, schema_editor):
    """Ensure all attribute slugs are unique.

    Instead of being unique within a product type, attributes' slug are now globally
    unique. For that, we look for duplicate slugs and rename them with a new suffix.
    """
    Attribute = apps.get_model("product", "Attribute")  # noqa
    non_unique_slugs = (
        Attribute.objects.values_list("slug", flat=True)
        .annotate(slug_count=Count("slug"))
        .filter(slug_count__gt=1)
    )
    non_unique_attrs = Attribute.objects.filter(slug__in=list(non_unique_slugs))
    for suffix, attr in enumerate(non_unique_attrs):
        attr.slug += f"__{suffix}"
        attr.save(update_fields=["slug"])


def remove_duplicates_products_in_collections(apps, schema_editor):
    """Remove any duplicated M2M, and keep only one of them.

    First we select the duplicates, by grouping them and counting them:

        SELECT
            collection_id, product_id, COUNT(*)
        FROM
            public.product_collectionproduct
        GROUP BY
            collection_id, product_id
        HAVING
            COUNT(*) > 1

    Then we retrieve all of them except one (LIMIT = `duplicate_count - 1`).

    Once we have them, we delete each of them manually (cannot directly delete by using
    LIMIT).
    """

    CollectionProduct = apps.get_model("product", "CollectionProduct")

    duplicates = (
        CollectionProduct.objects.values("collection_id", "product_id")
        .annotate(duplicate_count=Count("*"))
        .filter(duplicate_count__gt=1)
    )

    for duplicate in duplicates:
        dup_count = duplicate.pop("duplicate_count")
        delete_limit = dup_count - 1
        entries_to_delete = CollectionProduct.objects.filter(**duplicate)[:delete_limit]
        for entry in entries_to_delete:
            entry.delete()


@dataclass(frozen=True)
class NewCollectionProductSortOrder:
    pk: int
    sort_order: int


def ensure_model_is_ordered(model_name):
    def reorder_model(apps, schema_editor):
        model_cls = apps.get_model("product", "CollectionProduct")
        new_values = model_cls.objects.values("id").annotate(
            sort_order=Window(
                expression=RowNumber(),
                order_by=(F("sort_order").asc(nulls_last=True), "id"),
            )
        )

        batch = [NewCollectionProductSortOrder(*row.values()) for row in new_values]
        model_cls.objects.bulk_update(batch, ["sort_order"])

    return reorder_model


PRODUCT_TYPE_UNIQUE_SLUGS = [
    migrations.RunPython(ensure_attribute_slugs_are_unique_or_fix)
]

M2M_UNIQUE_TOGETHER = [migrations.RunPython(remove_duplicates_products_in_collections)]

SORTING_NULLABLE_LOGIC = [
    migrations.RunPython(ensure_model_is_ordered("AttributeValue")),
    migrations.RunPython(ensure_model_is_ordered("CollectionProduct")),
    migrations.RunPython(ensure_model_is_ordered("ProductImage")),
]


class Migration(migrations.Migration):

    dependencies = [("product", "0101_auto_20190719_0839")]

    operations = (
        PRODUCT_TYPE_UNIQUE_SLUGS + M2M_UNIQUE_TOGETHER + SORTING_NULLABLE_LOGIC
    )
