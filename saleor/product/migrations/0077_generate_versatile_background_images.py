# Generated by Django 2.1.2 on 2018-11-11 16:08
from sys import stderr

from django.db import migrations, models
from versatileimagefield.image_warmer import VersatileImageFieldWarmer


def log_failed_images(failed_to_create):
    if failed_to_create:
        print("Failed to generate thumbnails:", file=stderr)
        for path in failed_to_create:
            print(path, file=stderr)


def warm_model_background_images(model: models.Model):
    warmer = VersatileImageFieldWarmer(
        instance_or_queryset=model.objects.all(),
        rendition_key_set="background_images",
        image_attr="background_image",
        verbose=True,
    )
    num_created, failed_to_create = warmer.warm()
    log_failed_images(failed_to_create)


def warm_background_images(apps, *_):
    Category = apps.get_model("product", "Category")
    print("Generating thumbnails for Categories", file=stderr)
    warm_model_background_images(Category)

    Collection = apps.get_model("product", "Collection")
    print("Generating thumbnails for Collections", file=stderr)
    warm_model_background_images(Collection)


class Migration(migrations.Migration):

    dependencies = [("product", "0076_auto_20181012_1146")]

    operations = [migrations.RunPython(warm_background_images)]
