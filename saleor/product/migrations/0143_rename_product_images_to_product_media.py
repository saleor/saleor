# Generated by Django 3.1.5 on 2021-02-12 13:00

import django.db.models.deletion
import versatileimagefield.fields
from django.db import migrations, models

from ...product import ProductMediaTypes


def migrate_images_content_to_media(apps, _schema_editor):
    ProductImage = apps.get_model("product", "ProductImage")
    ProductMedia = apps.get_model("product", "ProductMedia")

    VariantImage = apps.get_model("product", "VariantImage")
    VariantMedia = apps.get_model("product", "VariantMedia")

    for image in ProductImage.objects.iterator():
        product_media, _ = ProductMedia.objects.get_or_create(
            product=image.product,
            image=image.image,
            alt=image.alt,
            ppoi=image.ppoi,
            sort_order=image.sort_order,
            type=ProductMediaTypes.IMAGE,
        )

        for variant_image in VariantImage.objects.filter(image__pk=image.id):
            VariantMedia.objects.get_or_create(
                variant=variant_image.variant, media=product_media
            )


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0142_auto_20210308_1135"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductMedia",
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
                    "sort_order",
                    models.IntegerField(db_index=True, editable=False, null=True),
                ),
                (
                    "image",
                    versatileimagefield.fields.VersatileImageField(
                        blank=True, null=True, upload_to="products"
                    ),
                ),
                (
                    "ppoi",
                    versatileimagefield.fields.PPOIField(
                        default="0.5x0.5", editable=False, max_length=20
                    ),
                ),
                ("alt", models.CharField(blank=True, max_length=128)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("IMAGE", "An uploaded image or an URL to an image"),
                            ("VIDEO", "A URL to an external video"),
                        ],
                        default="IMAGE",
                        max_length=32,
                    ),
                ),
                (
                    "external_url",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                ("oembed_data", models.JSONField(blank=True, default=dict)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media",
                        to="product.product",
                    ),
                ),
            ],
            options={
                "ordering": ("sort_order", "pk"),
            },
        ),
        migrations.CreateModel(
            name="VariantMedia",
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
                    "media",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variant_media",
                        to="product.productmedia",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="variantmedia",
            name="variant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="variant_media",
                to="product.productvariant",
            ),
        ),
        migrations.RunPython(
            migrate_images_content_to_media, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterUniqueTogether(
            name="variantimage",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="variantimage",
            name="image",
        ),
        migrations.RemoveField(
            model_name="variantimage",
            name="variant",
        ),
        migrations.RemoveField(
            model_name="productvariant",
            name="images",
        ),
        migrations.AddField(
            model_name="productvariant",
            name="media",
            field=models.ManyToManyField(
                through="product.VariantMedia", to="product.ProductMedia"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="variantmedia",
            unique_together={("variant", "media")},
        ),
        migrations.DeleteModel(
            name="ProductImage",
        ),
        migrations.DeleteModel(
            name="VariantImage",
        ),
    ]
