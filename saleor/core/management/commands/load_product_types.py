import csv

from django.core.management.base import BaseCommand

from saleor.product.models import Category, ProductType
from django.utils.text import slugify


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='category file path')

    def handle(self, *args, **options):

        self.load_product_types(options['path'])

    def load_product_types(self, path):
        with open(path, encoding="utf8", errors='ignore') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for rid, row in enumerate(reader):

                try:
                    categoryPath = '/' + slugify(row[0]) + '/' + slugify(
                        row[1]) + '/' + slugify(row[2])
                    metadata = {'categoryPath': categoryPath, 'description': row[5]}
                    productType = ProductType.objects.get(
                        name=row[4], metadata=metadata)

                except ProductType.DoesNotExist:

                    ProductType.objects.create(name=row[4], slug=slugify(row[1] + " " + row[2] + " " + row[4]),
                                               metadata=metadata)
