from __future__ import unicode_literals

import json
from django.db import migrations


def move_data(apps, schema_editor):
    CartLine = apps.get_model('cart', 'CartLine')
    for line in CartLine.objects.all():
        line.data_postgres = json.loads(line.data)
        line.save()

    Cart = apps.get_model('cart', 'Cart')
    for cart in Cart.objects.all():
        cart.checkout_data_postgres = json.loads(cart.checkout_data)
        cart.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_auto_20161209_0652'),
    ]

    operations = [
        migrations.RunPython(move_data)
    ]
