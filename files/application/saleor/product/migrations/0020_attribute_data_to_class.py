from __future__ import unicode_literals

from django.db import migrations, models


def move_data(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    ProductClass = apps.get_model('product', 'ProductClass')

    for product in Product.objects.all():
        attributes = product.attributes.all()
        product_class = ProductClass.objects.all()
        for attribute in attributes:
            product_class = product_class.filter(
                variant_attributes__in=[attribute])
        product_class = product_class.first()
        if product_class is None:
            product_class = ProductClass.objects.create(
                name='Unnamed product type',
                has_variants=True)
            product_class.variant_attributes = attributes
            product_class.save()
        product.product_class = product_class
        product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0019_auto_20161212_0230'),
    ]

    operations = [
        migrations.RunPython(move_data),
    ]
