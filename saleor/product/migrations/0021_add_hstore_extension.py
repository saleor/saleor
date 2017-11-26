from __future__ import unicode_literals

from django.db import migrations
from django.contrib.postgres.operations import HStoreExtension


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0020_attribute_data_to_class'),
    ]

    operations = [
        HStoreExtension(),
    ]
