from django.db import migrations


def assign_sort_order_to_variant_media(apps, schema_editor):
    ProductVariant = apps.get_model("product", "ProductVariant")
    VariantMedia = apps.get_model("product", "VariantMedia")
    for variant in ProductVariant.objects.iterator(chunk_size=2000):
        variant_media_qs = VariantMedia.objects.filter(variant=variant).order_by("pk")
        for order, variant_media in enumerate(variant_media_qs):
            variant_media.sort_order = order
            variant_media.save(update_fields=["sort_order"])


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0206_alter_variantmedia_options_variantmedia_sort_order"),
    ]

    operations = [
        migrations.RunPython(
            assign_sort_order_to_variant_media, migrations.RunPython.noop
        ),
    ]
