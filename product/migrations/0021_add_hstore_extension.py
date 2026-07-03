from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("product", "0020_attribute_data_to_class")]

    operations = [HStoreExtension()]
