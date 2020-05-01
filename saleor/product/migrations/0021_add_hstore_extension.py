from __future__ import unicode_literals

from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations

from saleor.core.hstore import h_store_extension


class Migration(migrations.Migration):

    dependencies = [("product", "0020_attribute_data_to_class")]

    operations = [h_store_extension]
