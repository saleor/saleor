from django.contrib.postgres.fields import jsonb
from django.core import exceptions
from django.db import migrations, models


def validate_attribute_json(value):
    for k, values in value.items():
        if not isinstance(k, str):
            raise exceptions.ValidationError(
                f"The key {k!r} should be of type str (got {type(k)})",
                params={"k": k, "values": values},
            )
        if not isinstance(values, list):
            raise exceptions.ValidationError(
                f"The values of {k!r} should be of type list (got {type(values)})",
                params={"k": k, "values": values},
            )

        for value_pk in values:
            if not isinstance(value_pk, str):
                raise exceptions.ValidationError(
                    f"The values inside {value_pk!r} should be of type str "
                    f"(got {type(value_pk)})",
                    params={"k": k, "values": values, "value_pk": value_pk},
                )


def migrate_fk_to_m2m(product_type_related_field):
    """Migrate product types' foreign key to a M2M relation."""

    def make_migration(apps, schema):
        ProductType = apps.get_model("product", "ProductType")

        for product_type in ProductType.objects.all():
            m2m_field = getattr(product_type, product_type_related_field)
            attributes_to_migrate = getattr(
                product_type, f"{product_type_related_field}_old"
            )
            for attr in attributes_to_migrate.all():
                if product_type not in m2m_field.all():
                    m2m_field.add(attr)

    return make_migration


PRODUCT_TYPE_UNIQUE_SLUGS = [
    migrations.AlterField(
        model_name="attribute", name="slug", field=models.SlugField(unique=True)
    )
]

ATTRIBUTE_NEW_FIELDS = [
    migrations.AddField(
        model_name="attribute",
        name="input_type",
        field=models.CharField(
            choices=[("dropdown", "Dropdown"), ("multiselect", "Multi Select")],
            default="dropdown",
            max_length=50,
        ),
    ),
    migrations.AlterField(
        model_name="product",
        name="attributes",
        field=jsonb.JSONField(
            blank=True, default=dict, validators=[validate_attribute_json]
        ),
    ),
    migrations.AlterField(
        model_name="productvariant",
        name="attributes",
        field=jsonb.JSONField(
            blank=True, default=dict, validators=[validate_attribute_json]
        ),
    ),
    migrations.AddField(
        model_name="attribute",
        name="available_in_grid",
        field=models.BooleanField(blank=True, default=True),
    ),
    migrations.AddField(
        model_name="attribute",
        name="visible_in_storefront",
        field=models.BooleanField(default=True, blank=True),
    ),
    migrations.AddField(
        model_name="attribute",
        name="filterable_in_dashboard",
        field=models.BooleanField(default=True, blank=True),
    ),
    migrations.AddField(
        model_name="attribute",
        name="filterable_in_storefront",
        field=models.BooleanField(default=True, blank=True),
    ),
    migrations.AddField(
        model_name="attribute",
        name="value_required",
        field=models.BooleanField(default=False, blank=True),
    ),
    migrations.AddField(
        model_name="attribute",
        name="storefront_search_position",
        field=models.IntegerField(default=0, blank=True),
    ),
    migrations.AlterModelOptions(
        name="attribute", options={"ordering": ("storefront_search_position", "slug")}
    ),
]

PRODUCT_TYPE_NEW_RELATION = [
    migrations.AddField(
        model_name="attribute",
        name="is_variant_only",
        field=models.BooleanField(default=False, blank=True),
    ),
    # Rename the foreign keys to backup them before overriding and processing them
    migrations.RenameField(
        model_name="attribute", old_name="product_type", new_name="product_type_old"
    ),
    migrations.RenameField(
        model_name="attribute",
        old_name="product_variant_type",
        new_name="product_variant_type_old",
    ),
    # Rename related names of foreign keys
    migrations.AlterField(
        model_name="attribute",
        name="product_type_old",
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=models.deletion.CASCADE,
            related_name="product_attributes_old",
            to="product.ProductType",
        ),
    ),
    migrations.AlterField(
        model_name="attribute",
        name="product_variant_type_old",
        field=models.ForeignKey(
            blank=True,
            null=True,
            on_delete=models.deletion.CASCADE,
            related_name="variant_attributes_old",
            to="product.ProductType",
        ),
    ),
    # Add the M2M new fields
    migrations.CreateModel(
        name="AttributeProduct",
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
                "attribute",
                models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="attributeproduct",
                    to="product.Attribute",
                ),
            ),
            (
                "product_type",
                models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="attributeproduct",
                    to="product.ProductType",
                ),
            ),
            (
                "sort_order",
                models.IntegerField(db_index=True, editable=False, null=True),
            ),
        ],
        options={"abstract": False},
    ),
    migrations.CreateModel(
        name="AttributeVariant",
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
                "attribute",
                models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="attributevariant",
                    to="product.Attribute",
                ),
            ),
            (
                "product_type",
                models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="attributevariant",
                    to="product.ProductType",
                ),
            ),
            (
                "sort_order",
                models.IntegerField(db_index=True, editable=False, null=True),
            ),
        ],
        options={"abstract": False},
    ),
    migrations.AddField(
        model_name="attribute",
        name="product_types",
        field=models.ManyToManyField(
            blank=True,
            related_name="product_attributes",
            through="product.AttributeProduct",
            to="product.ProductType",
        ),
    ),
    migrations.AddField(
        model_name="attribute",
        name="product_variant_types",
        field=models.ManyToManyField(
            blank=True,
            related_name="variant_attributes",
            through="product.AttributeVariant",
            to="product.ProductType",
        ),
    ),
    # Migrate the foreign keys into M2M
    migrations.RunPython(migrate_fk_to_m2m("product_attributes")),
    migrations.RunPython(migrate_fk_to_m2m("variant_attributes")),
    # Remove the migrated foreign keys
    migrations.RemoveField(model_name="attribute", name="product_variant_type_old"),
    migrations.RemoveField(model_name="attribute", name="product_type_old"),
]

SORTING_NULLABLE_LOGIC = [
    migrations.AlterField(
        model_name="attributevalue",
        name="sort_order",
        field=models.IntegerField(db_index=True, editable=False, null=True),
    ),
    migrations.AlterField(
        model_name="collectionproduct",
        name="sort_order",
        field=models.IntegerField(db_index=True, editable=False, null=True),
    ),
    migrations.AlterField(
        model_name="productimage",
        name="sort_order",
        field=models.IntegerField(db_index=True, editable=False, null=True),
    ),
    migrations.AlterModelOptions(
        name="attributevalue", options={"ordering": ("sort_order", "id")}
    ),
]

M2M_UNIQUE_TOGETHER = [
    migrations.AlterUniqueTogether(
        name="attributeproduct", unique_together={("attribute", "product_type")}
    ),
    migrations.AlterUniqueTogether(
        name="attributevariant", unique_together={("attribute", "product_type")}
    ),
    migrations.AlterUniqueTogether(
        name="collectionproduct", unique_together={("collection", "product")}
    ),
]


class Migration(migrations.Migration):
    dependencies = [("product", "0102_migrate_data_enterprise_grade_attributes")]

    operations = (
        PRODUCT_TYPE_UNIQUE_SLUGS
        + ATTRIBUTE_NEW_FIELDS
        + PRODUCT_TYPE_NEW_RELATION
        + SORTING_NULLABLE_LOGIC
        + M2M_UNIQUE_TOGETHER
    )
