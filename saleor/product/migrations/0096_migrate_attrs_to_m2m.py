# Generated by Django 2.2.2 on 2019-06-12 08:15

from django.db import migrations, models


def migrate_fk_to_m2m(product_type_related_field):
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


class Migration(migrations.Migration):

    dependencies = [("product", "0095_auto_20190618_0842")]

    operations = [
        migrations.AddField(
            model_name="attribute",
            name="is_variant_only",
            field=models.BooleanField(default=False),
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
        # whether the attribute is visible in storefront
        migrations.AddField(
            model_name="attribute",
            name="visible_in_storefront",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="attribute",
            name="filterable_in_dashboard",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="attribute",
            name="filterable_in_storefront",
            field=models.BooleanField(default=True),
        ),
    ]
