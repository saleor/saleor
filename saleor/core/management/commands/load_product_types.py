import csv

from django.core.management.base import BaseCommand

from saleor.product.models import Category, ProductType
from django.utils.text import slugify


class Command(BaseCommand):

    FILE_PATH = 'filepath'


    def handle(self, *args, **options):

        self.load_product_types()



    def load_product_types(self):
        with open(self.FILE_PATH, encoding="utf8", errors='ignore') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for rid, row in enumerate(reader):

                try:
                    productType = ProductType.objects.get(name=row[4])
                except ProductType.DoesNotExist:


                    categoryPath = slugify(row[0]) + '/' + slugify(row[1]) + '/' + slugify(row[2])

                    metadata = {'categoryPath': categoryPath, 'description': row[5]}



                    ProductType.objects.create(name=row[4], slug=slugify(row[4]), metadata=metadata)

